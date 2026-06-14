from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path
from typing import Any, Literal

from tabulate import tabulate

OutputFormat = Literal["csv", "txt", "html"]


def normalize_output_format(output_format: str) -> OutputFormat:
    """입력된 출력 형식 문자열을 소문자로 변환하고, 유효한 형식(csv, txt, html)인지 검사하여 반환합니다."""
    normalized = output_format.lower()

    if normalized not in ("csv", "txt", "html"):
        raise ValueError("출력 형식은 csv, txt, html 중 하나여야 합니다.")

    return normalized  # type: ignore[return-value]


def get_repository_name(result: dict[str, Any]) -> str:
    """결과 딕셔너리에서 저장소 이름(owner/repo)을 추출하여 반환합니다."""
    return str(result["nameWithOwner"])


def get_issue_count(result: dict[str, Any]) -> int:
    """결과 딕셔너리에서 전체 이슈 개수를 추출하여 반환합니다."""
    return int(result["issues"]["totalCount"])


def get_pull_request_count(result: dict[str, Any]) -> int:
    """결과 딕셔너리에서 전체 PR 개수를 추출하여 반환합니다."""
    return int(result["pullRequests"]["totalCount"])


def build_txt_output(results: list[dict[str, Any]]) -> str:
    """조회된 결과 데이터를 표 형태의 텍스트(txt) 형식으로 변환하여 반환합니다."""
    has_score = any("totalScore" in result for result in results)

    headers = ["repo", "issues", "pull_requests"] + (
        ["total_score"] if has_score else []
    )

    rows = [
        [
            get_repository_name(result),
            get_issue_count(result),
            get_pull_request_count(result),
        ]
        + ([result.get("totalScore", 0)] if has_score else [])
        for result in results
    ]

    return tabulate(rows, headers=headers)


def build_csv_output(results: list[dict[str, Any]]) -> str:
    """조회된 결과 데이터를 콤마로 구분된 CSV 형식 문자열로 변환하여 반환합니다."""
    has_score = any("totalScore" in result for result in results)

    output = StringIO()
    writer = csv.writer(output)

    headers = ["repo", "issues", "pull_requests"] + (
        ["total_score"] if has_score else []
    )
    writer.writerow(headers)

    for result in results:
        writer.writerow(
            [
                get_repository_name(result),
                get_issue_count(result),
                get_pull_request_count(result),
            ]
            + ([result.get("totalScore", 0)] if has_score else [])
        )

    return output.getvalue().strip()


def build_html_output(results: list[dict[str, Any]]) -> str:
    """조회된 결과 데이터를 바탕으로 Chart.js를 사용한 HTML 막대 그래프 문서를 생성하여 반환합니다."""
    has_score = any("totalScore" in result for result in results)

    labels = []
    issues_data = []
    prs_data = []

    for result in results:
        name = get_repository_name(result)
        if has_score:
            score = result.get("totalScore", 0)
            labels.append(f"{name} (점수: {score})")
        else:
            labels.append(name)

        issues_data.append(get_issue_count(result))
        prs_data.append(get_pull_request_count(result))

    chart_height = max(400, len(results) * 40)

    labels_json = json.dumps(labels).replace("<", "\\u003c").replace(">", "\\u003e")
    issues_json = json.dumps(issues_data)
    prs_json = json.dumps(prs_data)

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>reposcore-py result</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels"></script>
  <style>
    .chart-container {{
      position: relative;
      height: {chart_height}px;
      width: 100%;
    }}
  </style>
</head>
<body>
  <div class="chart-container">
    <canvas id="myChart"></canvas>
  </div>
  <script>
    Chart.register(ChartDataLabels);
    const ctx = document.getElementById('myChart').getContext('2d');
    new Chart(ctx, {{
      type: 'bar',
      data: {{
        labels: {labels_json},
        datasets: [
          {{
            label: 'Issues',
            data: {issues_json},
            backgroundColor: 'rgba(255, 99, 132, 0.5)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 1
          }},
          {{
            label: 'Pull Requests',
            data: {prs_json},
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
          }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {{
          datalabels: {{
            color: '#000',
            anchor: 'end',
            align: 'right',
            offset: 4
          }}
        }},
        scales: {{
          x: {{
            beginAtZero: true
          }}
        }}
      }}
    }});
  </script>
</body>
</html>"""


def build_output(results: list[dict[str, Any]], output_format: str) -> str:
    """지정된 형식(txt, csv, html)에 맞춰 결과 데이터를 문자열로 변환하여 반환합니다."""
    normalized_format = normalize_output_format(output_format)

    if normalized_format == "csv":
        return build_csv_output(results)

    if normalized_format == "html":
        return build_html_output(results)

    return build_txt_output(results)


def write_output(
    content: str,
    output_dir: str,
    output_format: str,
) -> Path:
    """변환된 문자열 내용을 지정된 디렉터리에 해당 형식의 확장자를 가진 파일로 저장하고 파일 경로를 반환합니다."""
    normalized_format = normalize_output_format(output_format)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    result_path = output_path / f"results.{normalized_format}"
    result_path.write_text(content, encoding="utf-8")

    return result_path
