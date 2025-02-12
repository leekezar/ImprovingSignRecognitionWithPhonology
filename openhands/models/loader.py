import omegaconf
import torch.nn as nn


def load_encoder(encoder_cfg, in_channels):
    if encoder_cfg.type == "cnn3d":
        from .encoder.cnn3d import CNN3D

        return CNN3D(in_channels=in_channels, **encoder_cfg.params)
    
    elif encoder_cfg.type == "cnn2d":
        from .encoder.cnn2d import CNN2D

        return CNN2D(in_channels=in_channels, **encoder_cfg.params)
    
    elif encoder_cfg.type == "i3d":
        from .encoder.i3d import LayersPoseLocalI3d
        return LayersPoseLocalI3d(
            in_channels=in_channels,
            **encoder_cfg.params
            )

    #### GRAPH MODELS FOR POSE ####
    elif encoder_cfg.type == "pose-flattener":
        from .encoder.graph.pose_flattener import PoseFlattener

        return PoseFlattener(in_channels=in_channels, **encoder_cfg.params)
    elif encoder_cfg.type == "decoupled-gcn":
        from .encoder.graph.decoupled_gcn import DecoupledGCN

        return DecoupledGCN(in_channels=in_channels, **encoder_cfg.params)
    elif encoder_cfg.type == "st-gcn":
        from .encoder.graph.st_gcn import STGCN

        return STGCN(in_channels=in_channels, **encoder_cfg.params)
    elif encoder_cfg.type == "sgn":
        from .encoder.graph.sgn import SGN

        return SGN(in_channels=in_channels, **encoder_cfg.params)
    elif encoder_cfg.type == "gcn":
        from .encoder.graph.gcn import GCNModel
        from .encoder.graph.pose_flattener import PoseFlattener

        return nn.Sequential(
            GCNModel(in_channels=in_channels, **encoder_cfg.params),
            PoseFlattener(
                in_channels=in_channels,
                num_points=encoder_cfg.params.num_points,
            ),
        )
    else:
        raise ValueError(f"Encoder Type '{encoder_cfg.type}' not supported.")

def load_decoder(decoder_cfg, num_class, encoder, params = None):
    # # TODO: better way
    # if isinstance(encoder, nn.Sequential):
    #     n_out_features = encoder[-1].n_out_features
    # else:
    #     n_out_features = encoder.n_out_features

    n_out_features = encoder.n_out_features

    if decoder_cfg.type == "fc":
        from .decoder.fc import FC

        return FC(
            n_features=n_out_features, num_class=num_class, **decoder_cfg.params
        )

    if decoder_cfg.type == "param_fc":
        from .decoder.fc import NParamFC

        return NParamFC(
            n_features=n_out_features, num_class=num_class, params=params, 
            **decoder_cfg.params
        )

    elif decoder_cfg.type == "rnn":
        from .decoder.rnn import RNNClassifier

        return RNNClassifier(
            n_features=n_out_features, num_class=num_class, **decoder_cfg.params
        )
    elif decoder_cfg.type == "bert":
        from .decoder.bert_hf import BERT

        return BERT(
            n_features=n_out_features,
            num_class=num_class,
            config=decoder_cfg.params,
        )
    elif decoder_cfg.type == "fine_tuner":
        from .decoder.fine_tuner import FineTuner

        return FineTuner(
            n_features=n_out_features, num_class=num_class, **decoder_cfg.params
        )
    else:
        raise ValueError(f"Decoder Type '{decoder_cfg.type}' not supported.")

def load_ssl_backbone(cfg, in_channels, num_class):
    if cfg.type == 'dpc':
        from .ssl.dpc_rnn import DPC_RNN_Finetuner, load_weights_from_pretrained
        # Load pretraining config
        pretraining_cfg = omegaconf.OmegaConf.load(cfg.load_from.cfg_file)
        pretraining_cfg.in_channels = in_channels
        # Create model
        model = DPC_RNN_Finetuner(num_class=num_class, **pretraining_cfg.model)
        # Load weights
        model = load_weights_from_pretrained(model, cfg.load_from.ckpt)
        return model
    else:
        raise ValueError(f"SSL Type '{cfg.type}' not supported.")

def get_model(config, in_channels, num_class, params = None):
    if "pretrained" in config:
        # Load self-supervised backbone
        return load_ssl_backbone(config.pretrained, in_channels, num_class)

    encoder = load_encoder(config.encoder, in_channels)
    decoder = load_decoder(config.decoder, num_class, encoder, params)

    if not params:
        from .network import Network
        return Network(encoder, decoder)
    else:
        from .network import NNetwork
        return NNetwork(encoder, decoder)
