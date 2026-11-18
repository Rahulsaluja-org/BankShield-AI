import re
import unicodedata

MAX_INPUT_LENGTH = 4000

BLOCK_RULES = [
    ('CRED_01', 'credential_theft', 'CRITICAL', r'\b(?:steal|obtain|extract|harvest|retrieve|reveal|give me|show me|find|get)\b.{0,100}\b(?:someone else.s|another (?:person.s|user.s|customer.s)|other (?:people.s|users.|customers.)|victim.s)\b.{0,100}\b(?:passwords?|usernames?|logins?|credentials?|pins?|otps?|one.time (?:passwords?|codes?)|recovery codes?|session tokens?)\b', 'Request seeks another person’s authentication information.'),
    ('CRED_02', 'credential_theft', 'CRITICAL', r'\b(?:passwords?|pins?|otps?|credentials?|usernames?|logins?|recovery codes?|session tokens?)\b.{0,70}\b(?:of|for|belonging to|from)\b.{0,30}\b(?:another (?:user|person|customer)|someone else|other (?:users|customers)|a victim)\b', 'Request targets another person’s credentials.'),
    ('CRED_03', 'credential_theft', 'HIGH', r'\b(?:steal|harvest|capture|intercept|exfiltrate)\b.{0,70}\b(?:passwords?|credentials?|otps?|pins?|login details?|session cookies?|tokens?)\b', 'Credential theft or interception requested.'),
    ('MAL_01', 'malware', 'CRITICAL', r'\b(?:write|create|build|develop|deploy|spread|distribute|run)\b.{0,55}\b(?:ransomware|keylogger|banking trojan|credential stealer)\b', 'Creation or deployment of harmful malware requested.'),
    ('MAL_02', 'malware', 'CRITICAL', r'\b(?:encrypt|lock)\b.{0,65}\b(?:bank|victim|customer|company).{0,35}\b(?:files?|systems?|data)\b.{0,80}\b(?:ransom|payment|extort)\b', 'Ransomware-style extortion requested.'),
    ('DATA_01', 'data_exfiltration', 'CRITICAL', r'\b(?:steal|exfiltrate|dump|leak|extract|download)\b.{0,70}\b(?:customer|client|bank|account holder).{0,40}\b(?:records?|data|database|details?|information)\b', 'Unauthorised extraction of banking/customer information.'),
    ('DATA_02', 'data_exfiltration', 'HIGH', r'\b(?:show|reveal|give|send|list)\b.{0,55}\b(?:confidential|private|secret|internal)\b.{0,50}\b(?:customer|bank|account|financial)\b.{0,30}\b(?:data|records?|details?|information)\b', 'Disclosure of confidential banking information requested.'),
    ('FRAUD_01', 'financial_fraud', 'CRITICAL', r'\b(?:transfer|move|withdraw|take|send)\b.{0,60}\b(?:money|funds|cash)\b.{0,80}\b(?:without (?:their|the owner.s) (?:permission|consent)|from someone else.s|from another (?:person.s|customer.s|user.s))\b', 'Unauthorised financial transaction requested.'),
    ('FRAUD_02', 'financial_fraud', 'HIGH', r'\b(?:bypass|evade|disable|defeat)\b.{0,60}\b(?:fraud (?:detection|checks?|monitoring)|payment verification|transaction (?:verification|limits?|monitoring))\b', 'Evasion of banking fraud controls requested.'),
    ('ACCESS_01', 'unauthorised_access', 'CRITICAL', r'\b(?:bypass|defeat|circumvent|disable)\b.{0,50}\b(?:mfa|2fa|two.factor authentication|multi.factor authentication|otp|login verification|bank security)\b.{0,95}\b(?:someone else.s|another (?:person.s|customer.s|user.s)|without (?:permission|authorisation|authorization)|to (?:steal|access|break into))\b', 'Bypassing security for unauthorised access.'),
    ('ACCESS_02', 'unauthorised_access', 'HIGH', r'\b(?:hack|break into|gain (?:unauthori[sz]ed )?access to|compromise)\b.{0,65}\b(?:someone else.s|another (?:person.s|user.s|customer.s)|a victim.s)\b.{0,35}\b(?:bank|account|login)\b', 'Unauthorised account access requested.'),
    ('PHISH_01', 'phishing', 'CRITICAL', r'\b(?:write|create|draft|generate|make|build)\b.{0,65}\b(?:phishing (?:email|message|page|site)|fake bank (?:email|login|page|website)|fraudulent bank (?:email|message|site))\b', 'Creation of phishing content requested.'),
    ('PHISH_02', 'phishing', 'HIGH', r'\b(?:trick|deceive|fool|manipulate|impersonate)\b.{0,80}\b(?:customers?|account holders?|bank staff|users?)\b.{0,95}\b(?:otp|password|pin|credentials?|login|transfer|money|funds)\b', 'Social engineering targeting banking users.'),
    ('INJECT_01', 'prompt_injection', 'HIGH', r'\b(?:ignore|override|disregard|forget)\b.{0,35}\b(?:previous|prior|system|developer|safety|security)\b.{0,30}\b(?:instructions?|rules?|prompts?|guardrails?)\b', 'Instruction to override the assistant’s safeguards.'),
    ('INJECT_02', 'prompt_injection', 'HIGH', r'\b(?:disable|turn off|remove|bypass)\b.{0,35}\b(?:guardrails?|safety (?:checks?|filters?)|content filters?|security rules?)\b', 'Attempt to disable safety controls.'),
]

REVIEW_RULES = [
    ('REVIEW_ACCESS', 'security_testing', 'MEDIUM', r'\b(?:hack|exploit|penetration test|pentest|vulnerability scan|sql injection|brute.force|bypass (?:authentication|login|mfa|2fa))\b', 'Security testing or attack terminology needs context.'),
    ('REVIEW_FRAUD', 'financial_fraud', 'MEDIUM', r'\b(?:evade detection|avoid detection|hide transactions?|money laundering|fake identity|identity theft)\b', 'Potential financial crime context.'),
    ('REVIEW_DATA', 'sensitive_data', 'MEDIUM', r'\b(?:share|provide|send|display|list|reveal)\b.{0,55}\b(?:account numbers?|card numbers?|sort codes?|cvvs?|bank statements?)\b', 'Request may involve sensitive banking information.'),
]


DEFENSIVE_CONTEXT = re.compile(r'\b(?:what is|what are|explain|define|how (?:do|does|can|should) (?:banks?|customers?|users?|organisations?|organizations?|we|i) (?:detect|prevent|protect|defend|respond|recover|recognise|recognize|avoid|secure)|best practices?|warning signs?|awareness|incident response|mitigat(?:e|ion)|protect(?:ion|ing)?|defen[cs]e|recover(?:y)?|with (?:permission|authori[sz]ation)|authori[sz]ed (?:testing|audit|assessment))\b', re.I)


def _result(decision, reason, category='none', severity='NONE', rule_id=None):
    return {'decision': decision, 'reason': reason, 'category': category,
            'severity': severity, 'rule_id': rule_id}

def check_input(user_input: str) -> dict:
    if not isinstance(user_input, str) or not user_input.strip():
        return _result('BLOCK', 'Input is empty or invalid.', 'validation', 'LOW', 'VALID_01')
    if len(user_input) > MAX_INPUT_LENGTH:
        return _result('HUMAN_REVIEW', 'Input exceeds the configured length limit.', 'validation', 'MEDIUM', 'VALID_02')
    text = unicodedata.normalize('NFKC', user_input).casefold()
    text = re.sub(r'\s+', ' ', text)
    for rule_id, category, severity, pattern, reason in BLOCK_RULES:
        if re.search(pattern, text, re.I):
            return _result('BLOCK', reason, category, severity, rule_id)
    if DEFENSIVE_CONTEXT.search(text):
        return _result('ALLOW', 'Defensive or educational context; no explicit high-risk rule matched.', 'defensive_education', 'LOW', 'SAFE_01')
    for rule_id, category, severity, pattern, reason in REVIEW_RULES:
        if re.search(pattern, text, re.I):
            return _result('HUMAN_REVIEW', reason, category, severity, rule_id)
    return _result('ALLOW', 'No configured risk rule matched.')


if __name__ == '__main__':
    for prompt in ['How can banks detect phishing attacks?', 'Write ransomware to lock bank files.', 'How can I hack a bank account?', 'Give me another customer\'s bank username and password.']:
        print(prompt, '=>', check_input(prompt))
