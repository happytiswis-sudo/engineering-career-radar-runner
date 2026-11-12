"""Conservative mandatory-qualification gate grounded in the candidate's completed degree.

A hard exclusion requires clear mandatory wording, and must not fire for
preferred/optional qualifications, bachelor-or-master alternatives, or incomplete
BA search snippets lacking such wording. No AI model can override this gate.
"""
from __future__ import annotations
import re
import html

MASTER=r"(?:master(?:'s|s)?(?:\s+of\s+(?:science|engineering|arts))?(?:\s+degree|\s+abschluss)?|m\.?sc\.?|m\.?eng\.?|masterabschluss|masterstudium|masterstudiengang|mastergrad)"
MANDATORY=[
    re.compile(r"(?:must\s+(?:have|hold|possess)|requires?|mandatory|minimum(?:\s+qualification)?|essential|prerequisite|compulsory|need(?:ed)?|qualification\s*:)\s*(?:an?\s+|a\s+completed\s+)?"+MASTER,re.I),
    re.compile(MASTER+r"\s*(?:is\s+)?(?:required|mandatory|essential|a\s+must|minimum|necessary|obligatory)",re.I),
    re.compile(r"(?:abgeschlossen(?:es|en|er)?|erforderlich(?:es|en|er)?|vorausgesetzt(?:es|en|er)?|zwingend(?:es|en|er)?|mindestens|pflicht)\s+(?:\w+\s+){0,3}"+MASTER,re.I),
    re.compile(MASTER+r"\s*(?:zwingend|vorausgesetzt|erforderlich|benotigt|notwendig|pflicht)",re.I),
    re.compile(r"(?:abschluss|degree|qualifikation)\s*:\s*"+MASTER,re.I)
]
ALTERNATIVE=re.compile(r"(?:bachelor|b\.?sc\.?|b\.?eng\.?|undergraduate|diplom|equivalent\s+(?:qualification|experience|degree))",re.I)
OPTIONAL=re.compile(r"(?:preferred|desirable|advantage|nice\s+to\s+have|ideally|idealerweise|von\s+vorteil|wunschenswert|bevorzugt|optional|plus\b|nicht\s+zwingend|or\s+equivalent\s+experience)",re.I)
PHD=r"(?:ph\.?d\.?|doctorate|doctoral\s+degree|promotion|doktorgrad)"
PHD_REQUIRED=re.compile(PHD+r"\s*(?:is\s+)?(?:required|mandatory|essential|erforderlich|zwingend)|(?:must\s+have|requires?|mandatory|minimum)\s+(?:a\s+)?"+PHD,re.I)

def qualification_gate(text, highest_completed='bachelor'):
    if highest_completed not in ('bachelor','master','doctorate'):
        return {'status':'review','reasons':[],'evidence':[]}
    raw=html.unescape(re.sub(r'<[^>]*>',' ',str(text or '')))
    # More than one job requirement per line is common; work at clause scope.
    segments=re.split(r'[\n\r•;]|(?<=[.!?])\s+',raw)
    reasons=[]; evidence=[]
    for segment in segments:
        seg=re.sub(r'\s+',' ',segment).strip()
        if len(seg)>440:
            # Avoid very broad mixed-requirements paragraphs.
            continue
        if highest_completed=='bachelor' and re.search(MASTER,seg,re.I):
            if OPTIONAL.search(seg):continue
            if ALTERNATIVE.search(seg):continue
            if any(p.search(seg) for p in MANDATORY):
                reasons.append('Mandatory completed Master\'s degree not demonstrated by CV')
                evidence.append(seg[:230])
        if highest_completed in ('bachelor','master') and PHD_REQUIRED.search(seg):
            if OPTIONAL.search(seg) or ALTERNATIVE.search(seg):continue
            reasons.append('Mandatory doctorate/PhD not demonstrated by CV')
            evidence.append(seg[:230])
    return {'status':'excluded' if reasons else 'review','reasons':list(dict.fromkeys(reasons)),
            'evidence':list(dict.fromkeys(evidence))[:3]}
