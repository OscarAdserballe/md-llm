1. All cli-side processing should be pushed into respective objects

E.g.
```python
if not files:
    print(colored(f"No processable files found in {file}", "red"))
    return
```


2. Provider-specific behaviour likewise inside responsehandler


3. Likely supporting more providers outside of Universal OpenAI wrapper a bit better....

4. Fixing vector_store: loooksl ike an issue of embedding limits of 2048 tokens, whereby most intereactions odn't get stored properly.


Central objects:
* FileProcessor 
* LLM
* ResponseHandler


