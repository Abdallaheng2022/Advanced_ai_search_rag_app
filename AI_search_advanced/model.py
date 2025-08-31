from transformers import AutoTokenizer, AutoModelForCausalLM

name = "gpt2"  # أو أي نموذج متوافق
tok = AutoTokenizer.from_pretrained(name)
model = AutoModelForCausalLM.from_pretrained(name)

system_message="""
Task: From raw HTML of a web search page, extract:
1) organic: an array of organic search results (no ads, no sponsored).
2) knowledge: an array of factual items (e.g., knowledge panel facts, FAQs).
Output :output should be json format 
Rules:
- Ignore ads/sponsored/paid sections.
- Only return items visible in the HTML text provided.
- Normalize whitespace, strip tags.
- Output EXACTLY this JSON schema:

{
  "organic": [
    {"title": "...", "url": "...", "snippet": "..."}
  ],
  "knowledge": [
    {"label": "...", "value": "..."}
  ]
}

Return ONLY JSON. No extra text.

### EXAMPLE 1
[HTML]
<div id="search">
  <div class="result">
    <a href="https://example.com/apple">Apple - Official Site</a>
    <p>Discover iPhone, iPad, Mac and more.</p>
  </div>
  <div class="result ad">Ad · Buy iPhone now</div>
  <div id="rhs">
    <div class="kp-header">Apple Inc.</div>
    <div class="kp-fact"><span>Founded:</span> 1976</div>
    <div class="kp-fact"><span>CEO:</span> Tim Cook</div>
  </div>
</div>
[/HTML]
[JSON]
{
  "organic": [
    {
      "title": "Apple - Official Site",
      "url": "https://example.com/apple",
      "snippet": "Discover iPhone, iPad, Mac and more."
    }
  ],
  "knowledge": [
    {"label": "Entity", "value": "Apple Inc."},
    {"label": "Founded", "value": "1976"},
    {"label": "CEO", "value": "Tim Cook"}
  ]
}
### END
Output :output should be json format 

### YOUR TURN
[HTML]
{{RAW_HTML_FROM_SEARCH_PAGE}}
[/HTML]
[JSON]
"""


model_name = "gpt2"  # كل عائلة gpt2 حدّها 1024 عادةً
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# مهم لـ GPT-2 لأنه بدون pad_token افتراضياً
tokenizer.pad_token = tokenizer.eos_token
model.config.pad_token_id = tokenizer.eos_token_id

prompt = f"""{system_message} <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Bing Search Page</title>
  <link rel="stylesheet" href="8zJ2TR6fJItHlaUEnPI.gz.css" type="text/css"/>
  <script type="text/javascript">
//<![CDATA[
_G.HT = new Date();
//]]>
  </script>
</head>
<body>
  <div class="b_algo">
    <h2><a href="https://www.nvidia.com/en-us/drivers/">Official NVIDIA Drivers</a></h2>
    <p>Download the latest official NVIDIA drivers.</p>
  </div>
  <div class="b_algo">
    <h2><a href="https://en.wikipedia.org/wiki/Nvidia">Nvidia - Wikipedia</a></h2>
    <p>Nvidia is an American technology company based in Santa Clara, California.</p>
  </div>
</body>
</html> """
        
inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=model.config.n_positions)

# لا تجعل input_length + max_new_tokens > n_positions
input_len = inputs["input_ids"].shape[1]
n_positions = model.config.n_positions  # غالباً 1024
max_new = min(100, max(0, n_positions - input_len))  # اضبطها حسب حاجتك

out_ids = model.generate(
    **inputs,
    max_new_tokens=60,            # استخدم max_new_tokens بدلاً من max_length
    do_sample=True,
    top_p=0.95,
    temperature=0.7,
    eos_token_id=tokenizer.eos_token_id
)
print(tokenizer.decode(out_ids[0], skip_special_tokens=True))