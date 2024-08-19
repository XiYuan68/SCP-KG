from transformers import AutoModelForCausalLM, AutoTokenizer

device = "cuda" # the device to load the model onto

# dir_model = "model/qwen2_0.5B"
# 至少要 1.5B 模型才能正确RAG
# dir_model = "../LLM/Qwen2-1.5B-Instruct"
dir_model = "/home/chenxiyuan/PetProjects/LLM/Qwen2-7B-Instruct-AWQ"
# dir_model = "/home/chenxiyuan/PetProjects/LLM/Qwen2-7B-Instruct"
# dir_model = "/home/chenxiyuan/PetProjects/LLM/Qwen2-1.5B-Instruct"
model = AutoModelForCausalLM.from_pretrained(
    dir_model,
    torch_dtype="auto",
    device_map="auto",
    local_files_only=True,
    )
tokenizer = AutoTokenizer.from_pretrained(
    dir_model,
    local_files_only=True,
    )

def chat(prompt: str = "说一个关于麦当劳的笑话") -> str:
    # prompt = "Give me a short introduction to large language model."
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    model_inputs = tokenizer([text], return_tensors="pt").to(device)

    generated_ids = model.generate(
        model_inputs.input_ids,
        max_new_tokens=512
    )
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    print(prompt)
    print(response)
    return response


def predict_scp_object(
    tag: list[str] = ['人形生物'],
    text_start: str = '',
    ) -> str:
    tag = '、'.join(tag)
    prompt = f'请根据以下内容，预测可能存在的SCP项目档案片段。特性标签：【{tag}】；开头内容：【{text_start}】。'
    return chat(prompt)

if __name__ == '__main__':
    chat('''
    特殊收容措施：一支由梵蒂冈圣遗物回收办公室卫兵组成的小队将永久驻扎在梵蒂冈古墓和地下墓穴的所有入口处并持有枪杀许可。隶属于MTF Zeta-9 "鼹鼠"的特攻队随时待命以便对废墟进行紧急探索。
    描述：SCP-5653为一有敌意半人形实体，收容于梵蒂冈古墓下方的梵蒂冈地下墓穴中。SCP-5653形似一高度畸形的意大利裔男性与一中东裔女性的混合体。由于难以获得样本，对于该实体的具体生物信息知之甚少，但据信它与已故的红衣主教1Greco和罗马教廷2本身有某种联系。
    请根据以上内容回答：SCP-5653和北京有关吗？
    ''')