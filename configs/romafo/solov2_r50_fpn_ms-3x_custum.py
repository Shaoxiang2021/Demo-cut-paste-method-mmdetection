# env parameters
MYVAR_OPTIM_LR = 1e-05
MYVAR_OPTIM_WD = 0.001
MAX_EPOCHS = 20
STAG_EPOCHS = 4
INTERVAL = 5
BATCH_SIZE = 4
BEGINN_EPOCHS_COSIN_LR = 10
END_ITERS_LINEAR_LR = 400

DATA_ROOT = '../data/synthetic_images/3_cpu_5000_4/'
TEST_FOLDER = 'test_usb'
TEST_ROOT = '../data/source_images/05_test/test/'
load_from = "../mmdetection/checkpoints/solov2_r50_fpn_3x_coco_20220512_125856-fed092d4.pth"
work_dir = '../results/solov2_3_cpu_5000_4'




_base_ = '../solov2/solov2_r50_fpn_ms-3x_coco.py'

default_hooks = dict(
    checkpoint=dict(
        interval=INTERVAL,
        max_keep_ckpts=1  # only keep latest 1 checkpoints
    ))

# model parameters
model = dict(mask_head=dict(num_classes=3))

# set classes
metainfo = dict(classes=('cylinder', 'plate', 'usb'), palatte=[(255, 0, 0), (0, 255, 0), (0, 0, 255)])

# load custom files
# custom_imports = dict(imports=["custom.augmentation"], allow_failed_imports=False)

# optimizer
optim_wrapper = dict(_delete_=True, type='OptimWrapper', optimizer = dict(type='AdamW', lr=MYVAR_OPTIM_LR, weight_decay=MYVAR_OPTIM_WD), clip_grad=None)

# param_scheduler
param_scheduler = [dict(type='LinearLR', start_factor=1e-07, by_epoch=False, begin=0, end=END_ITERS_LINEAR_LR), dict(type='CosineAnnealingLR', T_max=MAX_EPOCHS-BEGINN_EPOCHS_COSIN_LR, begin=BEGINN_EPOCHS_COSIN_LR, end=MAX_EPOCHS, by_epoch=True, convert_to_iter_based=True)]

# pipline for training, validation and test
train_pipeline = [
    dict(backend_args=None, type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True, with_mask=True),
    dict(
          keep_ratio=True,
          scales=[
              (
                  1333,
                  800,
              ),
              (
                  1333,
                  768,
              ),
              (
                  1333,
                  736,
              ),
              (
                  1333,
                  704,
              ),
              (
                  1333,
                  672,
              ),
              (
                  1333,
                  640,
              ),
          ],
          type='RandomChoiceResize'),
    dict(type='PhotoMetricDistortion', contrast_range=(0.75, 1.25), saturation_range=(0.75, 1.25)),
    dict(type='Sharpness', min_mag=0.5, max_mag=1.5),
    dict(type='GeomTransform', min_mag=0.0, max_mag=0.5),
    dict(type='RandomFlip', prob=0.5),
    dict(type='PackDetInputs'),
]

train_pipeline_stage_II = [
    dict(backend_args=None, type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True, with_mask=True),
    dict(
          keep_ratio=True,
          scales=[
              (
                  1333,
                  800,
              ),
              (
                  1333,
                  768,
              ),
              (
                  1333,
                  736,
              ),
              (
                  1333,
                  704,
              ),
              (
                  1333,
                  672,
              ),
              (
                  1333,
                  640,
              ),
          ],
          type='RandomChoiceResize'),
    dict(type='YOLOXHSVRandomAug'),
    dict(type='RandomFlip', prob=0.5),
    dict(type='PackDetInputs'),
]

test_pipeline = [
    dict(backend_args=None, type='LoadImageFromFile'),
    dict(keep_ratio=True, scale=(1333,800), type='Resize'),
    dict(type='LoadAnnotations', with_bbox=True, with_mask=True),
    dict(
        meta_keys=(
            'img_id',
            'img_path',
            'ori_shape',
            'img_shape',
            'scale_factor',
        ),
        type='PackDetInputs'),
]

val_pipeline = test_pipeline

# test dataloader parameters
test_dataloader = dict(
    batch_size=1,
    dataset = dict(
        ann_file=TEST_FOLDER+'/annotations.json',
        data_prefix=dict(img=TEST_FOLDER+'/'),
        data_root=TEST_ROOT,
        pipeline=test_pipeline,
        metainfo=metainfo)
        )

test_evaluator = dict(
    ann_file=TEST_ROOT+TEST_FOLDER+'/annotations.json',
    metric='segm',
    type='CocoMetric',
    outfile_prefix=work_dir)

# train dataloader parameters
train_cfg = dict(_delete_=True, max_epochs=MAX_EPOCHS, val_interval=INTERVAL, type='EpochBasedTrainLoop'), dynamic_intervals=[(MAX_EPOCHS - STAG_EPOCHS, 1)])

train_dataloader = dict(
    batch_size=BATCH_SIZE,
    dataset=dict(
        ann_file='train/annotations.json',
        data_prefix=dict(img='train/imgs/'),
        data_root=DATA_ROOT,
        pipeline=train_pipeline,
        metainfo=metainfo)
        )

# validation dataloader parameters
val_dataloader = dict(
    batch_size=1,
    dataset=dict(
        ann_file='val/annotations.json',
        data_prefix=dict(img='val/imgs/'),
        data_root=DATA_ROOT,
        pipeline=val_pipeline,
        metainfo=metainfo)
        )

val_evaluator = dict(
    ann_file=DATA_ROOT+'val/annotations.json',
    metric='segm',
    type='CocoMetric')

custom_hooks = [
    dict(
        type='PipelineSwitchHook',
        switch_epoch=MAX_EPOCHS - STAG_EPOCHS,
        switch_pipeline=train_pipeline_stage_II)
]
