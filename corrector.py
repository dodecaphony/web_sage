import torch
from sage.spelling_correction import T5ModelForSpellingCorruption, \
    RuM2M100ModelForSpellingCorrection, \
    AvailableCorrectors


class Corrector:
    def __init__(self):
        self.__t5_models = {
            AvailableCorrectors.sage_fredt5_large,
            AvailableCorrectors.sage_fredt5_distilled_95m,
            AvailableCorrectors.sage_mt5_large,
            AvailableCorrectors.fred_large,
            AvailableCorrectors.ent5_large,
        }
        self.__m2m100_models = {
            AvailableCorrectors.sage_m2m100_1B,
            AvailableCorrectors.m2m100_1B,
            AvailableCorrectors.m2m100_418M,
        }

    def correct(self, model_name: str, batches: []):
        corrector = None
        for model in self.__t5_models:
            if model_name == model.name:
                print(model_name)
                corrector = T5ModelForSpellingCorruption.from_pretrained(model.value)
        for model in self.__m2m100_models:
            if model_name == model.name:
                print(model_name)
                corrector = RuM2M100ModelForSpellingCorrection.from_pretrained(model.value)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        corrector.model.to(device)
        return [corrector.correct(batch)[0] for batch in batches]
