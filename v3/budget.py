"""Proxy token ledger, not an assertion about Arena's tokenizer or framing."""
import hashlib
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'.screen-deps'))
from tokenizers import Tokenizer
TOKENIZER_PATH=Path('/Users/louis/.ollama/models/blobs/sha256-0997f410c57a1f4e53b09e4be8f4a172d90edd9564368fb0847030937229b9f3')
TOKENIZER_SHA256='0997f410c57a1f4e53b09e4be8f4a172d90edd9564368fb0847030937229b9f3'
CAP=8192
FRAMING_RESERVE=40

class Budget:
    def __init__(self):
        if hashlib.sha256(TOKENIZER_PATH.read_bytes()).hexdigest()!=TOKENIZER_SHA256:
            raise ValueError('Tokenizer digest mismatch')
        self.tokenizer=Tokenizer.from_file(str(TOKENIZER_PATH))
        self.generated=0; self.observations=0; self.turns=0
    @property
    def used(self): return self.generated+self.observations+FRAMING_RESERVE*self.turns
    @property
    def remaining(self): return max(0,CAP-self.used-FRAMING_RESERVE)
    def generation(self,count):
        if not isinstance(count,int) or count<0: raise ValueError('Invalid generated token count')
        if count>self.remaining: raise ValueError('Model exceeded requested token allowance')
        self.generated+=count; self.turns+=1
    def observation(self,text):
        self.observations+=len(self.tokenizer.encode(text,add_special_tokens=False).ids)
    def snapshot(self):
        return dict(generated_tokens=self.generated,observation_tokens=self.observations,framing_reserve_tokens=FRAMING_RESERVE*self.turns,completion_accounted=self.used,remaining_predict=self.remaining,budget_exhausted=self.used>=CAP)
