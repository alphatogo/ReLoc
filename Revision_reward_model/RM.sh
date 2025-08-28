export CUDA_VISIBLE_DEVICES=0,1,2,3

accelerate launch --config_file=./accelerate_configs/deepspeed_zero2.yaml --main_process_port=29502 --num_processes 4 ./reward_modeling.py \
    --model_name_or_path Qwen/Qwen2.5-Coder-7B-Instruct \
    --dataset_name "<path_or_HF_name_of_your_revision_pair_dataset>"  \
    --output_dir Qwen2.5-Coder-7B  \
    --bf16 True \
    --per_device_train_batch_size 8 \
    --num_train_epochs 1 \
    --gradient_checkpointing True \
    --learning_rate 5.0e-6 \
    --logging_steps 25 \
    --eval_strategy steps \
    --eval_steps 500 \
    --save_steps 3000 \
    --max_length 2048 \
    --push_to_hub False \
    --optim paged_adamw_32bit \
    --warmup_ratio 0.05 \
    --lr_scheduler_type cosine \
