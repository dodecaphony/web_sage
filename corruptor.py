from sage.spelling_corruption import SBSCConfig, SBSCCorruptor
from sage.utils import DatasetsAvailable, \
    load_available_dataset_from_hf, \
    draw_and_save_errors_distributions_comparison_charts
from sage.spelling_corruption.sbsc.labeler import process_mistypings
from sage.spelling_corruption import CharAugConfig, CharAugCorruptor, WordAugConfig, WordAugCorruptor
from sage.pipeline import PipelineConfig
from sage.pipeline import AugmentationPipeline


class Corruptor:
    def __init__(self):
        self.__corruptors = {
            'char': (CharAugCorruptor, CharAugConfig),
            'word': (WordAugCorruptor, WordAugConfig)
        }

    @staticmethod
    def corrupt_with_sbsc(language: str, dataset: str, batches: []):
        """
        Patched sage/utils/data_load_utils.py --> line 37, added trust_remote_code=True)
        :param language:
        :param dataset:
        :param batches: []
        :return: batches: []
        """

        sources, corrections = load_available_dataset_from_hf(dataset, for_labeler=True, split="train")
        reference_stats, reference_confusion_matrix, reference_typos_cnt = process_mistypings(sources, corrections)
        config = SBSCConfig(
            lang=language,
            typos_count=reference_typos_cnt,
            stats=reference_stats,
            confusion_matrix=reference_confusion_matrix,
        )
        corruptor = SBSCCorruptor.from_config(config)
        result = [corruptor.corrupt(batch) for batch in batches]
        return result

    def corrupt_with_augmentex(self, level: str, unit_prob: float, min_aug: int, max_aug: int, seed: int, batches: []):
        """
        Corrupt with Augmentex
        :param level:
        :param unit_prob:
        :param min_aug:
        :param max_aug:
        :param seed:
        :param batches: []
        :return: batches: []
        """
        corruptor, cor_config = self.__corruptors[level]
        config = cor_config(
            unit_prob=unit_prob,  # proportion of characters that is going to undergo edits
            min_aug=min_aug,  # minimum number of edits
            max_aug=max_aug,  # maximum number of edits
        )
        corruptor = corruptor.from_config(config)
        result = [corruptor.corrupt(batch, seed=seed) for batch in batches]
        return result

    @staticmethod
    def corrupt_with_pipeline(methods: [], language: str,
                              unit_prob: str, min_aug: int,
                              max_aug: int, seed: int,
                              batches: [], dataset: str):
        """
        Corrupt with augmentex
        :param methods:
        :param language:
        :param unit_prob:
        :param min_aug:
        :param max_aug:
        :param seed:
        :param batches: []
        :param dataset:
        :return: batches: []
        """
        pipeline_config = PipelineConfig()
        pipeline_config.set_char_params(min_aug=min_aug, max_aug=max_aug, unit_prob=unit_prob)
        pipeline_config.set_sbsc_params(lang=language,
                                        dataset_name_or_path=dataset,
                                        dataset_split="test")
        pipeline = AugmentationPipeline(config=pipeline_config, shuffle=False)
        augmenters = {
            'char-augmentex': pipeline.add_char_augmenter,
            'word-augmentex': pipeline.add_word_augmenter,
            'SBSC': pipeline.add_sbsc_augmenter,
        }

        methods.remove('none')
        methods_order = {}
        for i, method in enumerate(methods):
            methods_order[i] = method
            augmenters[method]()

        pipeline.set_order([*range(len(methods))])
        result = [pipeline.augment(batch, seed=seed) for batch in batches]
        return result
