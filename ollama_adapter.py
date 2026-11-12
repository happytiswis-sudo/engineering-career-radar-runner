"""Isolated authenticated Ollama adapter; intentionally not production-wired."""
from __future__ import annotations
import json, os, time, urllib.error, urllib.request
from typing import Any, Callable
from urllib.parse import urlparse

ASSESSMENT_KEYS = {"fit_score","recommendation","summary","strengths","gaps",
 "work_authorization_note","degree_requirement","requirement_evidence","confidence"}
RECOMMENDATIONS={"apply":"Apply","stretch":"Stretch","skip":"Skip"}
DEGREES={"bachelor accepted","master required","master preferred","not stated","unclear"}
CONFIDENCE={"high","medium","low"}

class OllamaAdapterError(RuntimeError):
    """Safe adapter failure; message never includes token or prompt."""

def _endpoint(base_url):
    parsed=urlparse(base_url.strip())
    if parsed.scheme not in ("https","http") or not parsed.netloc:
        raise OllamaAdapterError("Invalid Ollama base URL")
    if parsed.scheme!="https" and parsed.hostname not in ("localhost","127.0.0.1"):
        raise OllamaAdapterError("Ollama remote endpoint must use HTTPS")
    return base_url.rstrip("/")+"/api/generate"

def validate_assessment(content: Any) -> dict:
    if isinstance(content,dict) and isinstance(content.get("response"),str):
        content=content["response"]
    if not isinstance(content,str) or not content.strip():
        raise OllamaAdapterError("Ollama assessment is empty")
    try: obj=json.loads(content.strip())
    except (ValueError,TypeError) as exc:
        raise OllamaAdapterError("Ollama returned malformed assessment JSON") from exc
    if not isinstance(obj,dict) or not ASSESSMENT_KEYS.issubset(obj):
        raise OllamaAdapterError("Ollama assessment does not match required schema")
    score=obj["fit_score"]
    if type(score) is not int or not 0<=score<=100:
        raise OllamaAdapterError("Ollama assessment score is invalid")
    rec=str(obj["recommendation"]).strip().lower()
    if rec not in RECOMMENDATIONS: raise OllamaAdapterError("Ollama recommendation is invalid")
    if not isinstance(obj["summary"],str) or len(obj["summary"])>300:
        raise OllamaAdapterError("Ollama summary is invalid")
    for key,cap in (("strengths",4),("gaps",4),("requirement_evidence",3)):
        value=obj[key]
        if not isinstance(value,list) or len(value)>cap or any(not isinstance(x,str) or len(x)>160 for x in value):
            raise OllamaAdapterError("Ollama assessment list is invalid")
    note=obj["work_authorization_note"]
    if not isinstance(note,str) or len(note)>230: raise OllamaAdapterError("Ollama work authorization note is invalid")
    degree=str(obj["degree_requirement"]).strip().lower()
    confidence=str(obj["confidence"]).strip().lower()
    if degree not in DEGREES or confidence not in CONFIDENCE:
        raise OllamaAdapterError("Ollama degree or confidence value is invalid")
    return {"score":score,"recommendation":RECOMMENDATIONS[rec],"summary":obj["summary"].strip(),
      "strengths":obj["strengths"],"gaps":obj["gaps"],"work_authorization_note":note.strip(),
      "degree_requirement":degree,"requirement_evidence":obj["requirement_evidence"],
      "confidence":confidence,"provider":"Ollama (isolated pilot)","model":"llama3.2"}

def assess(prompt: str, *, base_url=None, token=None, timeout_seconds=90,
           urlopen=urllib.request.urlopen) -> dict:
    base_url=base_url or os.getenv("OLLAMA_SPACE_URL","")
    token=token or os.getenv("OLLAMA_SPACE_TOKEN","")
    if not token: raise OllamaAdapterError("Ollama Space token is not configured")
    if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>24000:
        raise OllamaAdapterError("Assessment prompt is empty or exceeds size limit")
    body=json.dumps({"model":"llama3.2","prompt":prompt,"stream":False,"format":"json"}).encode()
    request=urllib.request.Request(_endpoint(base_url),data=body,
       headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
    started=time.monotonic()
    try:
        with urlopen(request,timeout=max(3,min(120,int(timeout_seconds)))) as response:
            data=json.loads(response.read().decode("utf-8"))
        result=validate_assessment(data)
    except urllib.error.HTTPError as exc:
        if exc.code in (401,403): raise OllamaAdapterError("Ollama Space authentication failed") from exc
        raise OllamaAdapterError("Ollama endpoint returned HTTP error") from exc
    except urllib.error.URLError as exc:
        if isinstance(getattr(exc,"reason",None),TimeoutError):
            raise OllamaAdapterError("Ollama request timed out") from exc
        raise OllamaAdapterError("Ollama endpoint request failed") from exc
    except (TimeoutError,): raise OllamaAdapterError("Ollama request timed out")
    except OSError as exc: raise OllamaAdapterError("Ollama endpoint transport failed") from exc
    except (ValueError,TypeError) as exc: raise OllamaAdapterError("Ollama returned an unreadable response") from exc
    result["latency_seconds"]=round(time.monotonic()-started,3)
    return result

def assess_with_fallback(prompt: str, *, fallback: Callable[[], dict], **ollama_options) -> dict:
    """Pilot recovery harness: use fallback on any adapter failure; never return partial Ollama data."""
    try:
        result=assess(prompt, **ollama_options)
        result["fallback_used"]=False
        return result
    except OllamaAdapterError:
        recovered=fallback()
        if not isinstance(recovered,dict):
            raise RuntimeError("Fallback provider returned an invalid assessment")
        recovered=dict(recovered)
        recovered["fallback_used"]=True
        recovered["fallback_reason"]="ollama_assessment_failed"
        return recovered
