import os

# base options
dist_params = dict(backend='nccl')
log_level = 'INFO'
load_from = None
resume_from = None
cudnn_benchmark = True

custom_imports = dict(imports=["geospatial_fm"])


### Configs
# data loader related
num_frames = int(os.getenv('NUM_FRAMES', 3))
img_size = int(os.getenv('IMG_SIZE', 224))
num_workers = int(os.getenv('DATA_LOADER_NUM_WORKERS', 2))

# model related
pretrained_weights_path = "/dccstor/geofm-finetuning/pretrain_ckpts/mae_weights/2023-04-29_21-50-47/epoch-725-loss-0.0365.pt"
num_layers = 12
patch_size = 16
embed_dim = 768
num_heads = 12
tubelet_size = 1

experiment = 'multiclass_six_bands'

work_dir = '/dccstor/geofm-finetuning/hls_cdl_six_bands/experiments/' + experiment
save_path = work_dir


gpu_ids = [0]
dataset_type = 'LULC'
# dataset_type = 'CustomDataset'
data_root = '/dccstor/geofm-finetuning/hls_cdl_six_bands/'  # changed data root folder

img_norm_cfg = dict(
    means=[524.299965, 852.201097, 987.414649, 2948.727491, 2712.733024, 1827.229407, 
           524.299965, 852.201097, 987.414649, 2948.727491, 2712.733024, 1827.229407, 
           524.299965, 852.201097, 987.414649, 2948.727491, 2712.733024, 1827.229407],
    stds=[294.751052, 370.654275, 596.312886, 858.965608, 955.384411, 938.537931, 
          294.751052, 370.654275, 596.312886, 858.965608, 955.384411, 938.537931,
          294.751052, 370.654275, 596.312886, 858.965608, 955.384411, 938.537931])

splits = {'train': data_root + "training_chips/training_data.txt",
          'val': data_root + "validation_chips/validation_data.txt",
          'test':data_root + "validation_chips/validation_data.txt"}    
    
bands = [0, 1, 2, 3, 4, 5]

tile_size = 224
orig_nsize = 512
crop_size = (tile_size, tile_size)
train_pipeline = [
    dict(type='LoadGeospatialImageFromFile', to_float32=True),
    dict(type='LoadGeospatialAnnotations', reduce_zero_label=False),
    dict(type='RandomFlip', prob=0.5),
    dict(type='ToTensor', keys=['img', 'gt_semantic_seg']),
    dict(type='TorchNormalize', **img_norm_cfg),
    dict(type='TorchRandomCrop', crop_size=crop_size),
    dict(type='Reshape', keys=['img'], new_shape=(len(bands), num_frames, tile_size, tile_size)),
    dict(type='Reshape', keys=['gt_semantic_seg'], new_shape=(1, tile_size, tile_size)),
    dict(type='CastTensor', keys=['gt_semantic_seg'], new_type="torch.LongTensor"),
    dict(type='Collect', keys=['img', 'gt_semantic_seg']),
]

val_pipeline = [
    dict(type='LoadGeospatialImageFromFile', to_float32=True),
    dict(type='LoadGeospatialAnnotations', reduce_zero_label=False),
    dict(type='ToTensor', keys=['img', 'gt_semantic_seg']),
    dict(type='TorchNormalize', **img_norm_cfg),
    dict(type='TorchRandomCrop', crop_size=crop_size),
    dict(type='Reshape', keys=['img'], new_shape=(len(bands), num_frames, tile_size, tile_size)),
    dict(type='Reshape', keys=['gt_semantic_seg'], new_shape=(1, tile_size, tile_size)),
    dict(type='CastTensor', keys=['gt_semantic_seg'], new_type="torch.LongTensor"),
    dict(type='Collect', keys=['img', 'gt_semantic_seg'],
         meta_keys=['img_info', 'ann_info', 'seg_fields', 'img_prefix', 'seg_prefix', 'filename', 'ori_filename', 'img',
                    'img_shape', 'ori_shape', 'pad_shape', 'scale_factor', 'img_norm_cfg', 'gt_semantic_seg']),

]

test_pipeline = [
    dict(type='LoadGeospatialImageFromFile', to_float32=True),
    dict(type='ToTensor', keys=['img']),
    dict(type='TorchNormalize', **img_norm_cfg),
    dict(type='Reshape', keys=['img'], new_shape=(len(bands), num_frames, -1, -1), look_up = {'2': 1, '3': 2}),
    dict(type='CastTensor', keys=['img'], new_type="torch.FloatTensor"),
    dict(type='CollectTestList', keys=['img'],
         meta_keys=['img_info', 'seg_fields', 'img_prefix', 'seg_prefix', 'filename', 'ori_filename', 'img',
                    'img_shape', 'ori_shape', 'pad_shape', 'scale_factor', 'img_norm_cfg']),
]

CLASSES=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)

data = dict(
    samples_per_gpu=8,
    workers_per_gpu=1,
    train=dict(
        type=dataset_type,
        # CLASSES=CLASSES,
        data_root=data_root,
        img_dir= data_root + "training_chips",
        ann_dir=data_root + "training_chips",
        pipeline=train_pipeline,
        img_suffix='_merged.tif',
        seg_map_suffix='.mask.tif',
        ignore_index=0,
        split = splits['train']
    ),
    val=dict(
        type=dataset_type,
        # CLASSES=CLASSES,
        data_root=data_root,
        img_dir= data_root + "validation_chips",
        ann_dir=data_root + "validation_chips",
        pipeline=test_pipeline,
        img_suffix='_merged.tif',
        seg_map_suffix='.mask.tif',
        ignore_index=0,
        split = splits['val']
    ),
    test=dict(
        type='LULC',
        # CLASSES=CLASSES,
        data_root=data_root,
        img_dir= data_root + "validation_chips",
        ann_dir=data_root + "validation_chips",
        pipeline=test_pipeline,
        img_suffix='_merged.tif',
        seg_map_suffix='.mask.tif',
        ignore_index=0,
        split = splits['test']))
        #gt_seg_map_loader_cfg=dict(nodata=-1, nodata_replace=2)))

# AdamW optimizer, no weight decay for position embedding & layer norm in backbone
optimizer = dict(type="Adam", lr=1.5e-5, betas=(0.9, 0.999),  weight_decay=0.05)
optimizer_config = dict(grad_clip=None)
lr_config = dict(
    policy="poly",
    warmup="linear",
    warmup_iters=1500,
    warmup_ratio=1e-6,
    power=1.0,
    min_lr=0.0,
    by_epoch=False,
)

log_config = dict(
    interval=10,
    hooks=[
        dict(type='TextLoggerHook'),
    ])

# This checkpoint config is later overwritten to allow for better logging in mmseg/apis/train.py l. 163
checkpoint_config = dict(
    # Config to set the checkpoint hook, Refer to https://github.com/open-mmlab/mmcv/blob/master/mmcv/runner/hooks/checkpoint.py for implementation.
    by_epoch=False,  # Whether count by epoch or not.
    interval=1700,
    out_dir=save_path)

evaluation = dict(interval=1700, metric='mIoU', pre_eval=True, save_best='mIoU')
reduce_train_set = dict(reduce_train_set=False)
reduce_factor = dict(reduce_factor=1)

optimizer_config = dict(grad_clip=None)


runner = dict(type='IterBasedRunner', max_iters=20000)
# workflow = [('train',1)]  # Workflow for runner. [('train', 1)] means there is only one workflow and the workflow named 'train' is executed once. The workflow trains the model by 40000 iterations according to the `runner.max_iters`.
workflow = [('train', 1),('val', 1)]

norm_cfg = dict(type='BN', requires_grad=True)

loss_weights_multi = [0, 0.0238394411670918, 0.141533235012755, 0.115825892857142, 0.140217079878826, 0.12416444913903, 0.095742291135204, 0.080351933195153, 0.02978515625, 0.042391139190051, 0.0293570870535714, 0.0372562699298469, 0.0336383250956632, 0.00158722496811224, 0.0206115553252551, 0.0174608816964285, 0.0662380381058673]



# model = dict(
#     type='TemporalEncoderDecoder',
#     pretrained='/home/workdir/hls_six_bands_weights/epoch-832-loss-0.0473.pt',
#     backbone=dict(
#         type='PretrainVisionTransformer',
#         #pretrained='/home/workdir/hls-model-weights/epoch-941-loss-0.0602.pt',
#         img_size=img_size,
#         patch_size=patch_size,
#         num_frames=num_frames,
#         tubelet_size=1,
#         in_chans=len(bands),
#         embed_dim=embed_dim,
#         depth=num_layers,
#         num_heads=num_heads,
#         decoder_embed_dim=int(embed_dim / 2),
#         decoder_depth=8,
#         decoder_num_heads=num_heads,
#         mlp_ratio=4.,
#         norm_pix_loss=False
#     ),
#     decode_head=dict(
#         num_classes=17,
#         in_channels=embed_dim*num_frames,
#         type='FCNHead',
#         in_index=-1,
#         channels=256,
#         num_convs=1,
#         concat_input=False,
#         dropout_ratio=0.1,
#         norm_cfg=norm_cfg,
#         align_corners=False,
#         loss_decode=dict(
#             type='DiceLoss', use_sigmoid=False, loss_weight=1, class_weight=loss_weights_multi))
#     ,
#     auxiliary_head=dict(
#         num_classes=17,
#         in_channels=embed_dim*num_frames,
#         type='FCNHead',
#         in_index=-1,
#         channels=256,
#         num_convs=2,
#         concat_input=False,
#         dropout_ratio=0.1,
#         norm_cfg=norm_cfg,
#         align_corners=False,
#         loss_decode=dict(
#             type='DiceLoss', use_sigmoid=False, loss_weight=1, class_weight=loss_weights_multi)),
#     train_cfg=dict(frozen=False),
#     test_cfg=dict(mode='slide', stride=(128, 128), crop_size=(224, 224), frozen=False)
# )

# output_embed_dim = embed_dim*num_frames
output_embed_dim = embed_dim

model = dict(
    type="TemporalEncoderDecoder",
    frozen_backbone=False,
    backbone=dict(
        type="TemporalViTEncoder",
        pretrained=pretrained_weights_path,
        img_size=img_size,
        patch_size=patch_size,
        num_frames=num_frames,
        tubelet_size=1,
        in_chans=len(bands),
        embed_dim=embed_dim,
        depth=num_layers,
        num_heads=num_heads,
        mlp_ratio=4.0,
        norm_pix_loss=False,
    ),
    neck=dict(
        type="ConvTransformerTokensToEmbeddingNeck",
        embed_dim=embed_dim*num_frames,
        output_embed_dim=output_embed_dim,
        drop_cls_token=True,
        Hp=img_size // patch_size,
        Wp=img_size // patch_size
    ),
    decode_head=dict(
        num_classes=17,
        in_channels=output_embed_dim,
        type="FCNHead",
        in_index=-1,
        channels=256,
        num_convs=1,
        concat_input=False,
        dropout_ratio=0.1,
        norm_cfg=norm_cfg,
        align_corners=False,
        loss_decode=dict(
            type='DiceLoss', use_sigmoid=False, class_weight=loss_weights_multi),
    ),
    auxiliary_head=dict(
        num_classes=17,
        in_channels=output_embed_dim,
        type="FCNHead",
        in_index=-1,
        channels=256,
        num_convs=2,
        concat_input=False,
        dropout_ratio=0.1,
        norm_cfg=norm_cfg,
        align_corners=False,
        loss_decode=dict(type='DiceLoss', use_sigmoid=False, class_weight=loss_weights_multi),
    ),
    train_cfg=dict(),
    test_cfg=dict(mode="slide", stride=(int(tile_size/2), int(tile_size/2)), crop_size=(tile_size, tile_size)),
)