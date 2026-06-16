"""Generate Work24-shaped mock job postings.

The output is intentionally deterministic so the admin mock loader can be run
multiple times without changing source_job_id values.
"""

from __future__ import annotations

import json
from pathlib import Path

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "data" / "mock_work24_jobs.json"

COMPANIES = [
    ("넥스트커머스", 510100001),
    ("브릿지테크", 510100002),
    ("핀업랩스", 510100003),
    ("클라우드링크", 510100004),
    ("데이터그로브", 510100005),
    ("모션페이", 510100006),
    ("픽셀스튜디오", 510100007),
    ("루트소프트", 510100008),
    ("코어플랫폼", 510100009),
    ("인사이트웍스", 510100010),
    ("그린에너지IT", 510100011),
    ("메디플로우", 510100012),
    ("에듀코어", 510100013),
    ("오토메이션랩", 510100014),
    ("마켓웨이브", 510100015),
    ("시큐어넷", 510100016),
    ("게임포지", 510100017),
    ("스마트팩토리온", 510100018),
    ("웰니스앱스", 510100019),
    ("비즈온클라우드", 510100020),
]

LOCATIONS = [
    ("서울 강남구", "서울특별시 강남구 테헤란로 123"),
    ("서울 구로구", "서울특별시 구로구 디지털로 300"),
    ("서울 마포구", "서울특별시 마포구 월드컵북로 45"),
    ("서울 금천구", "서울특별시 금천구 가산디지털1로 88"),
    ("경기 성남시", "경기도 성남시 분당구 판교역로 235"),
    ("경기 수원시", "경기도 수원시 영통구 광교로 156"),
    ("부산 해운대구", "부산광역시 해운대구 센텀중앙로 90"),
    ("대전 유성구", "대전광역시 유성구 대학로 99"),
]

TEMPLATES = [
    ("백엔드 개발자", "Java/Spring Boot", "솔루션·SI·CRM·ERP", "정보통신", (3200, 4200), (5200, 8200)),
    ("프론트엔드 개발자", "React/TypeScript", "포털·인터넷·콘텐츠", "정보통신", (3100, 4300), (5000, 7800)),
    ("풀스택 웹개발자", "Node.js/React", "소프트웨어개발", "정보통신", (3300, 4500), (5400, 8500)),
    ("모바일 앱개발자", "Kotlin/Swift", "모바일·APP", "정보통신", (3200, 4400), (5200, 8200)),
    ("데이터 엔지니어", "Python/Airflow", "데이터·AI", "정보통신", (3400, 4700), (5800, 9200)),
    ("AI 엔지니어", "Python/PyTorch", "인공지능·빅데이터", "정보통신", (3600, 5000), (6500, 11000)),
    ("DevOps 엔지니어", "AWS/Kubernetes", "클라우드·인프라", "정보통신", (3400, 4800), (6000, 9800)),
    ("QA·보안 엔지니어", "Selenium/OWASP", "정보보안·품질관리", "정보통신", (3100, 4300), (5200, 8600)),
    ("게임 서버 개발자", "C++/Unity", "게임·애니메이션", "문화콘텐츠", (3300, 4700), (5800, 9500)),
    ("ERP·SI 개발자", "Java/Oracle", "솔루션·SI·ERP", "정보통신", (3000, 4100), (4800, 7600)),
]


def main() -> None:
    wanted = [_make_wanted(i + 1, "신입") for i in range(50)]
    wanted.extend(_make_wanted(i + 1, "경력") for i in range(50))

    OUTPUT_PATH.write_text(
        json.dumps({"wantedRoot": {"wanted": wanted}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"generated {len(wanted)} mock jobs at {OUTPUT_PATH}")


def _make_wanted(index: int, career_type: str) -> dict[str, str]:
    template = TEMPLATES[(index - 1) % len(TEMPLATES)]
    company_name, business_seed = COMPANIES[(index - 1) % len(COMPANIES)]
    business_number = _business_number_from_seed(business_seed)
    region, address = LOCATIONS[(index - 1) % len(LOCATIONS)]
    job_no = index if career_type == "신입" else index + 50
    salary_range = template[4] if career_type == "신입" else template[5]
    min_salary, max_salary = salary_range
    min_salary_won = min_salary * 10000
    max_salary_won = max_salary * 10000
    min_career = 2 + (index % 6)
    career = "신입" if career_type == "신입" else f"경력 {min_career}년 이상"
    posted_day = (index % 20) + 1
    deadline_day = (index % 24) + 1
    title = f"{career_type} {template[0]} ({template[1]})"

    return {
        "wantedAuthNo": f"MOCK-{2000 + job_no}",
        "company": company_name,
        "busino": business_number,
        "indTpNm": template[2],
        "title": title,
        "region": region,
        "basicAddr": address,
        "detailAddr": f"{job_no}층",
        "career": career,
        "minEdubg": "초대졸 이상" if career_type == "신입" else "학력무관",
        "empTpCd": "10",
        "holidayTpNm": "주 5일·유연근무",
        "salTpNm": "연봉",
        "sal": f"{min_salary:,}만원~{max_salary:,}만원",
        "minSal": str(min_salary_won),
        "maxSal": str(max_salary_won),
        "regDt": f"2026-05-{posted_day:02d}",
        "closeDt": f"2026-06-{deadline_day:02d}",
        "smodifyDtm": f"2026-05-{posted_day:02d} 09:00:00",
        "wantedInfoUrl": f"https://demo.jobfit.local/jobs/MOCK-{2000 + job_no}",
        "wantedMobileInfoUrl": f"https://demo.jobfit.local/jobs/MOCK-{2000 + job_no}",
        "jobsCd": template[3],
        "jobCont": (
            f"{company_name}에서 {career_type} {template[0]}를 모집합니다. "
            f"{template[1]} 기반 서비스 개발, 운영 자동화, 성능 개선, 협업 프로세스 개선을 담당합니다."
        ),
    }


def _business_number_from_seed(first_nine_digits: int) -> str:
    digits = [int(ch) for ch in f"{first_nine_digits:09d}"]
    weights = [1, 3, 7, 1, 3, 7, 1, 3]
    total = sum(digit * weight for digit, weight in zip(digits[:8], weights))
    last_product = digits[8] * 5
    total += last_product // 10 + last_product % 10
    check_digit = (10 - (total % 10)) % 10
    return "".join(str(digit) for digit in [*digits, check_digit])


if __name__ == "__main__":
    main()
