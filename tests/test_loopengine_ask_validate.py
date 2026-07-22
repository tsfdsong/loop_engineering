import unittest

from loopengine_ask.validate import ValidationError, validate_ask_args


class ValidateAskArgsTest(unittest.TestCase):
    def test_ok_single_with_recommended_flag(self):
        out = validate_ask_args({
            "question": "选方案？",
            "options": [
                {"id": "a", "label": "A", "recommended": True},
                {"id": "b", "label": "B"},
            ],
        })
        self.assertFalse(out["multiSelect"])
        self.assertEqual(out["options"][0]["id"], "a")

    def test_ok_recommended_in_label(self):
        validate_ask_args({
            "question": "Q",
            "options": [
                {"label": "X (推荐)"},
                {"label": "Y"},
            ],
        })

    def test_reject_one_option(self):
        with self.assertRaises(ValidationError):
            validate_ask_args({"question": "Q", "options": [{"label": "only (推荐)"}]})

    def test_reject_five_options(self):
        opts = [{"label": f"o{i}", "recommended": i == 0} for i in range(5)]
        with self.assertRaises(ValidationError):
            validate_ask_args({"question": "Q", "options": opts})

    def test_reject_no_recommended(self):
        with self.assertRaises(ValidationError):
            validate_ask_args({
                "question": "Q",
                "options": [{"label": "A"}, {"label": "B"}],
            })

    def test_reject_empty_question(self):
        with self.assertRaises(ValidationError):
            validate_ask_args({
                "question": "  ",
                "options": [
                    {"label": "A (推荐)"},
                    {"label": "B"},
                ],
            })


if __name__ == "__main__":
    unittest.main()
