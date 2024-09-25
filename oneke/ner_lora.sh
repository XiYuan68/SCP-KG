josn_train='data/ner/train.json'
josn_test='data/ner/test.json'
output_dir='model/ner/'
model_path='../../LLM/OneKE/'
batch_size=16
epoch=3
val_size=100
save_steps=25
eval_steps=100
# batch size set for one 22G 2080Ti
torchrun --master_port=1287 InstructKGC/src/finetune.py \
    --do_train --do_eval \
    --overwrite_output_dir \
    --model_name_or_path ${model_path} \
    --stage 'sft' \
    --model_name 'llama' \
    --template 'llama2_zh' \
    --train_file ${josn_train} \
    --val_set_size ${val_size} \
    --output_dir ${output_dir} \
    --per_device_train_batch_size ${batch_size} \
    --per_device_eval_batch_size ${batch_size} \
    --gradient_accumulation_steps 1 \
    --preprocessing_num_workers 16 \
    --num_train_epochs ${epoch} \
    --learning_rate 5e-5 \
    --max_grad_norm 0.5 \
    --optim "adamw_torch" \
    --max_source_length 400 \
    --cutoff_len 700 \
    --max_target_length 300 \
    --evaluation_strategy "steps" \
    --eval_steps ${eval_steps} \
    --save_strategy "steps" \
    --save_steps ${save_steps} \
    --save_total_limit 10 \
    --lora_r 64 \
    --lora_alpha 64 \
    --lora_dropout 0.05 \
    --bf16 \
    --bits 4