import re
import unicodedata

MAX_OUTPUT_LENGTH = 10000

SECRET_RULES = [
    ('SECRET_PASSWORD', 'credential_leak', 'CRITICAL', r'\b(?:password|passwd|passcode|pin|otp|one.time password|recovery code)\s*[:=]\s*["\']?\S{4,}', 'Possible authentication secret disclosed.'),
    ('SECRET_API', 'api_secret_leak', 'CRITICAL', r'\b(?:api[_ -]?key|secret[_ -]?key|access[_ -]?token|private[_ -]?key|client[_ -]?secret)\s*[:=]\s*["\']?\S{8,}', 'Possible API key or access secret disclosed.'),
    ('SECRET_BEARER', 'token_leak', 'CRITICAL', r'\bauthorization\s*:\s*bearer\s+[a-z0-9._~+/-]{12,}', 'Possible bearer token disclosed.'),
]

DANGEROUS_RULES = [
    ('OUT_MALWARE', 'malware_instruction', 'HIGH', r'\b(?:write|deploy|execute|run|spread)\b.{0,55}\b(?:ransomware|keylogger|banking trojan|credential stealer)\b', 'Potentially harmful malware instructions.'),
    ('OUT_PHISH', 'phishing_instruction', 'HIGH', r'\b(?:trick|deceive|impersonate)\b.{0,65}\b(?:bank customers?|account holders?|bank staff)\b.{0,80}\b(?:password|otp|pin|credentials?|transfer)\b', 'Potential phishing or social-engineering instructions.'),
    ('OUT_BYPASS', 'security_bypass', 'HIGH', r'\b(?:disable|bypass|turn off|circumvent)\b.{0,35}\b(?:bank security|fraud detection|payment verification|mfa|2fa)\b.{0,60}\b(?:to avoid detection|without permission|to gain access|to steal)\b', 'Potentially unsafe bypass instructions.'),
]

BANK_DATA_RULES = [
    ('BANK_ACCOUNT', 'banking_data', 'MEDIUM', r'\b(?:account (?:number|no\.?|#)|sort code|iban)\s*[:=]\s*[a-z0-9][a-z0-9 -]{5,33}', 'Possible banking account information disclosed.'),
    ('BANK_CARD', 'payment_card', 'MEDIUM', r'\b(?:card (?:number|no\.?|#)|credit card|debit card)\s*[:=]\s*(?:\d[ -]?){13,19}\b', 'Possible payment card number disclosed.'),
]


def _result(decision, reason, category='none', severity='NONE', rule_id=None):
    return {'decision': decision, 'reason': reason, 'category': category,
            'severity': severity, 'rule_id': rule_id}

def check_output(model_output: str) -> dict:
    if not isinstance(model_output, str) or not model_output.strip():
        return _result('BLOCK', 'Output is empty or invalid.', 'validation', 'LOW', 'VALID_OUT_01')
    if len(model_output) > MAX_OUTPUT_LENGTH:
        return _result('HUMAN_REVIEW', 'Output exceeds configured inspection length.', 'validation', 'MEDIUM', 'VALID_OUT_02')
    text = unicodedata.normalize('NFKC', model_output)
    for rule_id, category, severity, pattern, reason in SECRET_RULES:
        if re.search(pattern, text, re.I):
            return _result('BLOCK', reason, category, severity, rule_id)
    for rule_id, category, severity, pattern, reason in DANGEROUS_RULES:
        if re.search(pattern, text, re.I):
            return _result('BLOCK', reason, category, severity, rule_id)
    for rule_id, category, severity, pattern, reason in BANK_DATA_RULES:
        if re.search(pattern, text, re.I):
            return _result('HUMAN_REVIEW', reason, category, severity, rule_id)
    return _result('ALLOW', 'No configured output risk rule matched.')


if __name__ == '__main__':
    for response in ['Banks should use MFA.', 'Password: SuperSecret123', 'Account number: 1234 5678 9012']:
        print(response, '=>', check_output(response))
