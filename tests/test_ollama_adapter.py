import io, json, unittest, urllib.error
from unittest.mock import Mock, patch
from ollama_adapter import OllamaAdapterError, assess, validate_assessment, assess_with_fallback

def payload():
 return {"fit_score":74,"recommendation":"Stretch","summary":"Relevant engineering role.","strengths":["CAD"],"gaps":["German C1"],"work_authorization_note":"Not stated.","degree_requirement":"bachelor accepted","requirement_evidence":["Bachelor degree"],"confidence":"medium"}

class OllamaAdapterTests(unittest.TestCase):
 def test_valid_schema_and_mapping(self):
  out=validate_assessment(json.dumps(payload())); self.assertEqual(out["score"],74); self.assertEqual(out["recommendation"],"Stretch")
 def test_accepts_ollama_wrapper(self): self.assertEqual(validate_assessment({"response":json.dumps(payload())})["score"],74)
 def test_rejects_malformed_json(self):
  with self.assertRaisesRegex(OllamaAdapterError,"malformed"): validate_assessment("{bad")
 def test_rejects_missing_keys(self):
  with self.assertRaisesRegex(OllamaAdapterError,"required schema"): validate_assessment(json.dumps({"fit_score":80}))
 def test_rejects_invalid_score_and_rec(self):
  bad=payload(); bad["fit_score"]=True
  with self.assertRaisesRegex(OllamaAdapterError,"score"): validate_assessment(json.dumps(bad))
  bad=payload(); bad["recommendation"]="Maybe"
  with self.assertRaisesRegex(OllamaAdapterError,"recommendation"): validate_assessment(json.dumps(bad))
 def test_auth_header_and_payload(self):
  class Response(io.BytesIO):
   def __enter__(self): return self
   def __exit__(self,*args): return False
  captured={}
  def fake(request,timeout):
   captured["req"]=request; captured["timeout"]=timeout
   return Response(json.dumps({"response":json.dumps(payload())}).encode())
  result=assess("synthetic prompt",base_url="https://example.test",token="secret",urlopen=fake)
  req=captured["req"]; body=json.loads(req.data.decode())
  self.assertEqual(req.get_header("Authorization"),"Bearer secret")
  self.assertEqual(body["format"],"json"); self.assertFalse(body["stream"]); self.assertIn("latency_seconds",result)
 def test_unexpected_transport_oserror_is_normalized(self):
  def fake(*args,**kwargs): raise OSError("connection reset")
  with self.assertRaisesRegex(OllamaAdapterError,"transport failed"): assess("prompt",base_url="https://example.test",token="secret",urlopen=fake)
 def test_auth_failure_fails_closed(self):
  def fake(*args,**kwargs): raise urllib.error.HTTPError("https://x",401,"unauthorized",{},None)
  with self.assertRaisesRegex(OllamaAdapterError,"authentication"): assess("prompt",base_url="https://example.test",token="secret",urlopen=fake)
 def test_malformed_response_fails_closed(self):
  class Response(io.BytesIO):
   def __enter__(self): return self
   def __exit__(self,*args): return False
  with self.assertRaisesRegex(OllamaAdapterError,"malformed"):
   assess("prompt",base_url="https://example.test",token="secret",urlopen=lambda *a,**k:Response(b'{"response":"no JSON"}'))
 def test_remote_http_rejected(self):
  with self.assertRaisesRegex(OllamaAdapterError,"HTTPS"): assess("prompt",base_url="http://example.test",token="secret")
 def test_timeout_recovers_to_fallback_without_ollama_partial(self):
  fallback=Mock(return_value={"score":51,"provider":"current-provider","recommendation":"Review"})
  with patch("ollama_adapter.assess",side_effect=OllamaAdapterError("timeout")): result=assess_with_fallback("prompt",fallback=fallback)
  fallback.assert_called_once_with(); self.assertEqual(result["score"],51); self.assertTrue(result["fallback_used"]); self.assertNotEqual(result["provider"],"Ollama (isolated pilot)")
 def test_malformed_output_recovers_to_fallback(self):
  fallback=Mock(return_value={"score":62,"provider":"current-provider"})
  with patch("ollama_adapter.assess",side_effect=OllamaAdapterError("malformed JSON")): result=assess_with_fallback("prompt",fallback=fallback)
  self.assertTrue(result["fallback_used"]); self.assertEqual(result["score"],62)
 def test_fallback_invalid_return_fails_closed(self):
  with patch("ollama_adapter.assess",side_effect=OllamaAdapterError("provider unavailable")):
   with self.assertRaisesRegex(RuntimeError,"invalid assessment"): assess_with_fallback("prompt",fallback=lambda:None)
if __name__=="__main__": unittest.main()
