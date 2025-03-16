from sage.spelling_corruption import SBSCConfig, SBSCCorruptor
from sage.utils import DatasetsAvailable, load_available_dataset_from_hf, draw_and_save_errors_distributions_comparison_charts
from sage.spelling_corruption.sbsc.labeler import process_mistypings

from sage.spelling_corruption import CharAugConfig, CharAugCorruptor, WordAugConfig, WordAugCorruptor


class Corruptor:
    def __init__(self):
        self.__corruptors = {
            'char': (CharAugCorruptor, CharAugConfig),
            'word': (WordAugCorruptor, WordAugConfig)
        }

    @staticmethod
    def corrupt_with_sbsc(language: str, dataset: str, content: str):
        """
        Patched sage/utils/data_load_utils.py --> line 37, added trust_remote_code=True)
        :param language:
        :param dataset:
        :param content:
        :return: text
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
        result = corruptor.corrupt(content)
        return result

    def corrupt_with_augmentex(self, level: str, unit_prob: float, min_aug: int, max_aug: int, content: str):
        """
        Corrupt with Augmentex
        :param level:
        :param unit_prob:
        :param min_aug:
        :param max_aug:
        :param content:
        :return: text
        """
        corruptor, cor_config = self.__corruptors[level]
        config = cor_config(
            unit_prob=unit_prob,  # proportion of characters that is going to undergo edits
            min_aug=min_aug,  # minimum number of edits
            max_aug=max_aug,  # maximum number of edits
        )
        corruptor = corruptor.from_config(config)
        result = corruptor.corrupt(content)  # add action
        return result

    def corrupt_with_pipeline(self):
        return
