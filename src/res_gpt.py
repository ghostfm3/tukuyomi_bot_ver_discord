from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

torch.set_default_tensor_type('torch.cuda.FloatTensor')
device = torch.device("cuda")
tokenizer = AutoTokenizer.from_pretrained("./model/model_xx")
tokenizer.do_lower_case = True 
model = AutoModelForCausalLM.from_pretrained("./model/model_xx").to(device) 
tokenizer.padding_side = "left"

def generate_reply(inp, num_gen=1):
    input_text = "<s>" + str(inp) + "[SEP]"
    input_ids = tokenizer.encode(input_text, return_tensors='pt')
    input_ids = input_ids.to(device)  
    out = model.generate(input_ids, do_sample=True, max_length=64, num_return_sequences=num_gen, 
                         top_p=0.925, top_k=20, bad_words_ids=[[1], [5]], no_repeat_ngram_size=3)

    for sent in tokenizer.batch_decode(out):
        sent = sent.split('[SEP]</s>')[1]
        sent = sent.replace('</s>', '')
        sent = sent.replace('<br>', '\n')
    
    return sent