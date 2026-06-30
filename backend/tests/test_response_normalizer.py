from __future__ import annotations

import unittest

from app.response_normalizer import ResponseNormalizer


class ResponseNormalizerTest(unittest.TestCase):
    def test_trim_sentence_does_not_leave_trailing_comma(self) -> None:
        text = "源石病是一种由源石引发的感染，它会侵蚀感染者的身体。"

        trimmed = ResponseNormalizer._trim_sentence(text, max_chars=18)

        self.assertEqual(trimmed, "源石病是一种由源石引发的感染")

    def test_trim_sentence_keeps_sentence_ending_punctuation(self) -> None:
        text = "请先休息。任务可以稍后再处理。"

        trimmed = ResponseNormalizer._trim_sentence(text, max_chars=8)

        self.assertEqual(trimmed, "请先休息。")


if __name__ == "__main__":
    unittest.main()
