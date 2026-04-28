import pytest

from llm.parsers.code_parser import CodeBlock, CodeOutputParser
from llm.parsers.json_parser import JsonOutputParser
from llm.parsers.schemas.prose_output import ProseGenerationOutput


VALID_PROSE_JSON = """
{
  "classifiers": [
    {
      "name": "Loan",
      "type": "class",
      "attributes": [
        {
          "name": "amount",
          "type": "int",
          "enum": null,
          "derived": false,
          "description": "Requested loan amount",
          "body": null
        }
      ]
    },
    {
      "name": "Applicant",
      "type": "class",
      "attributes": [
        {
          "name": "income",
          "type": "int",
          "enum": null,
          "derived": false,
          "description": "Applicant income",
          "body": null
        }
      ]
    }
  ],
  "relations": [
    {
      "source": "Loan",
      "target": "Applicant",
      "type": "association",
      "multiplicity": {
        "source": "1",
        "target": "1"
      }
    }
  ]
}
"""


@pytest.mark.parametrize(
    "raw_response",
    [
        VALID_PROSE_JSON,
        "```json\n" + VALID_PROSE_JSON + "\n```",
        "Here is the response:\n" + VALID_PROSE_JSON + "\nThanks.",
    ],
)
def test_json_parser_accepts_clean_fenced_and_preamble_json(raw_response):
    parser = JsonOutputParser(ProseGenerationOutput)

    result = parser.parse(raw_response)

    assert result.success is True
    assert isinstance(result.data, ProseGenerationOutput)
    assert result.data.classifiers[0].name == "Loan"
    assert result.error is None


def test_json_parser_reports_empty_response():
    parser = JsonOutputParser(ProseGenerationOutput)

    result = parser.parse("")

    assert result.success is False
    assert result.error.code == "EMPTY_RESPONSE"


def test_json_parser_reports_no_json_text_as_decode_error():
    parser = JsonOutputParser(ProseGenerationOutput)

    result = parser.parse("There is no JSON in this response.")

    assert result.success is False
    assert result.error.code == "JSON_DECODE_ERROR"


def test_json_parser_reports_json_decode_error_for_truncated_json():
    parser = JsonOutputParser(ProseGenerationOutput)

    result = parser.parse('{ "classifiers": [')

    assert result.success is False
    assert result.error.code == "JSON_DECODE_ERROR"


def test_json_parser_reports_schema_validation_error_for_wrong_schema():
    parser = JsonOutputParser(ProseGenerationOutput)

    raw_response = """
    {
      "classifiers": [
        {
          "name": "Loan",
          "type": "Class",
          "attributes": []
        }
      ],
      "relations": []
    }
    """

    result = parser.parse(raw_response)

    assert result.success is False
    assert result.error.code == "SCHEMA_VALIDATION_ERROR"
    assert result.error.details["errors"]


def test_code_parser_accepts_python_fenced_code():
    parser = CodeOutputParser()

    raw_response = "```python\ndef risk_score(self):\n    return 1\n```"

    result = parser.parse(raw_response)

    assert result.success is True
    assert isinstance(result.data, CodeBlock)
    assert result.data.is_valid_python is True
    assert "def risk_score" in result.data.code


def test_code_parser_accepts_no_fence_valid_python():
    parser = CodeOutputParser()

    raw_response = "def risk_score(self):\n    return 1"

    result = parser.parse(raw_response)

    assert result.success is True
    assert result.data.is_valid_python is True


def test_code_parser_rejects_explanation_plus_code_as_syntax_error():
    parser = CodeOutputParser()

    raw_response = "Here is the code:\n\ndef risk_score(self):\n    return 1"

    result = parser.parse(raw_response)

    assert result.success is False
    assert result.error.code == "PYTHON_SYNTAX_ERROR"
    assert result.data.is_valid_python is False
    assert "Here is the code" in result.raw_response


def test_code_parser_reports_python_syntax_error():
    parser = CodeOutputParser()

    raw_response = "```python\ndef risk_score(self):\n    return self.\n```"

    result = parser.parse(raw_response)

    assert result.success is False
    assert result.error.code == "PYTHON_SYNTAX_ERROR"
    assert result.error.details["message"]


def test_code_parser_reports_short_plain_text():
    parser = CodeOutputParser()

    result = parser.parse("Done")

    assert result.success is False
    assert result.error.code == "SHORT_RESPONSE"
