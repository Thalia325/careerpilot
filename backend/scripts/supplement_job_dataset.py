from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.reference import (  # noqa: E402
    filter_computer_related_rows,
    get_job_dataset_metadata,
    load_job_postings_dataset,
    normalize_job_dataset_row,
    normalize_job_title,
)


HEADERS = [
    "title",
    "location",
    "salary_range",
    "company_name",
    "industry",
    "company_size",
    "ownership_type",
    "job_code",
    "description",
    "company_intro",
    "source_url",
    "updated_at",
]

DEFAULT_EXTRA_KEYWORDS = [
    "前端开发",
    "Java",
    "C/C++",
    "软件测试",
    "测试工程师",
    "技术支持工程师",
    "实施工程师",
    "运维工程师",
    "数据分析",
    "算法工程师",
    "产品经理",
    "项目经理",
    "网络安全",
    "嵌入式",
    "通信工程师",
    "售前技术支持",
    "售后技术支持",
    "解决方案工程师",
    "人工智能",
    "机器学习",
]

TITLE_CANONICAL_RULES: list[tuple[tuple[str, ...], str]] = [
    (("前端", "开发"), "前端开发"),
    (("web前端",), "前端开发"),
    (("java",), "Java"),
    (("c/c++",), "C/C++"),
    (("c++",), "C/C++"),
    (("硬件测试",), "硬件测试"),
    (("芯片测试",), "硬件测试"),
    (("射频测试",), "硬件测试"),
    (("软件测试",), "软件测试"),
    (("测试", "工程师"), "测试工程师"),
    (("测试开发",), "测试工程师"),
    (("质量管理",), "质量管理/测试"),
    (("质检",), "质检员"),
    (("实施", "工程师"), "实施工程师"),
    (("技术支持",), "技术支持工程师"),
    (("fae",), "技术支持工程师"),
    (("售前", "技术支持"), "技术支持工程师"),
    (("售后", "技术支持"), "技术支持工程师"),
    (("产品", "专员"), "产品专员/助理"),
    (("产品", "助理"), "产品专员/助理"),
    (("项目", "专员"), "项目专员/助理"),
    (("项目", "助理"), "项目专员/助理"),
    (("项目", "招投标"), "项目招投标"),
    (("项目", "经理"), "项目经理/主管"),
    (("运营", "专员"), "运营助理/专员"),
    (("运营", "助理"), "运营助理/专员"),
    (("社区运营",), "社区运营"),
    (("游戏运营",), "游戏运营"),
    (("游戏推广",), "游戏推广"),
    (("app推广",), "APP推广"),
    (("内容审核",), "内容审核"),
    (("商务", "专员"), "商务专员"),
    (("bd",), "BD经理"),
    (("大客户",), "大客户代表"),
    (("销售工程师",), "销售工程师"),
    (("销售运营",), "销售运营"),
    (("广告销售",), "广告销售"),
    (("网络销售",), "网络销售"),
    (("电话销售",), "电话销售"),
    (("销售", "助理"), "销售助理"),
    (("售后", "客服"), "售后客服"),
    (("网络客服",), "网络客服"),
    (("电话客服",), "电话客服"),
    (("咨询顾问",), "咨询顾问"),
    (("培训师",), "培训师"),
    (("招聘", "专员"), "招聘专员/助理"),
    (("猎头", "顾问"), "猎头顾问"),
    (("储备经理",), "储备经理人"),
    (("储备干部",), "储备干部"),
    (("管培生",), "管培生/储备干部"),
    (("总助",), "总助/CEO助理/董事长助理"),
    (("ceo助理",), "总助/CEO助理/董事长助理"),
    (("董事长助理",), "总助/CEO助理/董事长助理"),
    (("知识产权",), "知识产权/专利代理"),
    (("专利代理",), "知识产权/专利代理"),
    (("法务",), "法务专员/助理"),
    (("律师助理",), "律师助理"),
    (("律师",), "律师"),
    (("统计",), "统计员"),
    (("科研",), "科研人员"),
    (("博士后",), "科研人员"),
    (("档案管理",), "档案管理"),
    (("资料管理",), "资料管理"),
    (("英语", "翻译"), "英语翻译"),
    (("日语", "翻译"), "日语翻译"),
    (("风电", "工程师"), "风电工程师"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Supplement A13 job dataset with additional computer-related jobs.")
    parser.add_argument(
        "--dataset",
        default=None,
        help="Base official dataset path. Defaults to current configured dataset.",
    )
    parser.add_argument(
        "--target-multiplier",
        type=float,
        default=2.0,
        help="Target filtered dataset multiplier after supplementation. Default doubles the current usable rows.",
    )
    parser.add_argument(
        "--max-city-count",
        type=int,
        default=30,
        help="How many top cities from the current dataset to use as crawl seeds.",
    )
    parser.add_argument(
        "--max-keyword-count",
        type=int,
        default=24,
        help="How many job titles/keywords to use as crawl seeds.",
    )
    parser.add_argument(
        "--max-pages-per-query",
        type=int,
        default=5,
        help="Max result pages per city-keyword query.",
    )
    parser.add_argument(
        "--detail-workers",
        type=int,
        default=8,
        help="Concurrent workers for job detail fetching.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.15,
        help="Sleep interval between list page requests.",
    )
    parser.add_argument(
        "--supplement-output",
        default=str(PROJECT_DIR / "data" / "a13_jobs_supplement.csv"),
        help="Output CSV path for new supplemental jobs.",
    )
    parser.add_argument(
        "--merged-output",
        default=str(PROJECT_DIR / "data" / "a13_jobs_augmented.csv"),
        help="Output CSV path for merged official + supplemental jobs.",
    )
    return parser.parse_args()


def _http_get(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def _extract_initial_state(html_text: str) -> dict[str, Any]:
    match = re.search(r"__INITIAL_STATE__=(\{.*?\})</script>", html_text, re.S)
    if not match:
        raise ValueError("Unable to locate __INITIAL_STATE__ in page")
    return json.loads(match.group(1))


def _clean_html_text(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</div>|</p>|</li>|</h\d>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _normalize_scraped_title(value: Any) -> str:
    return normalize_job_title(value)


def _city_from_location(location: str) -> str:
    text = str(location or "").strip()
    if not text:
        return ""
    return re.split(r"[-·•/]", text, maxsplit=1)[0].strip()


def _extract_city_map() -> dict[str, str]:
    state = _extract_initial_state(_http_get("https://www.zhaopin.com/citymap/"))
    city_map_list = state.get("cityList", {}).get("cityMapList", {})
    mapping: dict[str, str] = {}
    for group in city_map_list.values():
        for city in group:
            name = str(city.get("name", "")).strip()
            code = str(city.get("code", "")).strip()
            if name and code:
                mapping[name] = code
    return mapping


def _choose_seed_cities(rows: list[dict[str, Any]], city_codes: dict[str, str], max_count: int) -> list[tuple[str, str]]:
    counter = Counter(_city_from_location(row.get("location", "")) for row in rows)
    seeds: list[tuple[str, str]] = []
    for city_name, _ in counter.most_common():
        if not city_name:
            continue
        code = city_codes.get(city_name)
        if code:
            seeds.append((city_name, code))
        if len(seeds) >= max_count:
            break

    fallback_cities = ["北京", "上海", "深圳", "广州", "杭州", "成都", "西安", "苏州", "南京", "武汉"]
    for city_name in fallback_cities:
        code = city_codes.get(city_name)
        if code and (city_name, code) not in seeds:
            seeds.append((city_name, code))
        if len(seeds) >= max_count:
            break
    return seeds


def _choose_seed_keywords(rows: list[dict[str, Any]], max_count: int) -> list[str]:
    title_counter = Counter(str(row.get("title", "")).strip() for row in rows if str(row.get("title", "")).strip())
    keywords = [title for title, _ in title_counter.most_common(max_count)]
    for keyword in DEFAULT_EXTRA_KEYWORDS:
        if keyword not in keywords:
            keywords.append(keyword)
        if len(keywords) >= max_count:
            break
    return keywords[:max_count]


def _industry_text(item: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("industryName", "industryLevel", "industryNameLevel", "industry"):
        value = item.get(key)
        if value:
            parts.append(str(value))
    for entry in item.get("industryCompanyTags") or []:
        name = entry.get("name") if isinstance(entry, dict) else entry
        if name:
            parts.append(str(name))
    unique: list[str] = []
    seen: set[str] = set()
    for part in parts:
        cleaned = str(part).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique.append(cleaned)
    return ",".join(unique)


def _normalize_list_item(item: dict[str, Any]) -> dict[str, Any] | None:
    title = _normalize_scraped_title(item.get("name") or "")
    job_code = str(item.get("number") or item.get("jobNumber") or item.get("jobId") or "").strip()
    source_url = str(item.get("positionURL") or item.get("positionUrl") or "").strip().replace("http://", "https://")
    if not title or not job_code:
        return None

    location_parts = [str(item.get("workCity") or "").strip(), str(item.get("cityDistrict") or "").strip()]
    location = "-".join(part for part in location_parts if part)
    row = {
        "title": title,
        "location": location,
        "salary_range": str(item.get("salary60") or item.get("salaryReal") or "").strip(),
        "company_name": str(item.get("companyName") or "").strip(),
        "industry": _industry_text(item),
        "company_size": str(item.get("companySize") or "").strip(),
        "ownership_type": str(item.get("propertyName") or item.get("financingStage") or "").strip(),
        "job_code": job_code,
        "description": _clean_html_text(item.get("jobSummary") or ""),
        "company_intro": "",
        "source_url": source_url,
        "updated_at": str(item.get("publishTime") or item.get("firstPublishTime") or item.get("jobPostingTime") or "").strip(),
    }
    return normalize_job_dataset_row(row)


def _fetch_list_rows(city_code: str, keyword: str, max_pages: int, sleep_seconds: float) -> list[dict[str, Any]]:
    encoded_keyword = quote(keyword)
    rows: list[dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        suffix = f"/p{page}" if page > 1 else ""
        url = f"https://www.zhaopin.com/sou/jl{city_code}/kw{encoded_keyword}{suffix}"
        try:
            state = _extract_initial_state(_http_get(url))
        except Exception:
            break
        position_list = state.get("positionList") or []
        if not position_list:
            break
        for item in position_list:
            normalized = _normalize_list_item(item)
            if normalized:
                rows.append(normalized)
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    return rows


def _fetch_detail_enrichment(row: dict[str, Any]) -> dict[str, Any]:
    source_url = str(row.get("source_url") or "").strip()
    if not source_url:
        return row
    try:
        state = _extract_initial_state(_http_get(source_url))
    except Exception:
        return row

    job_detail = state.get("jobDetail") or {}
    company_detail = job_detail.get("detailedCompany") or {}
    position_detail = job_detail.get("detailedPosition") or {}

    enriched = dict(row)
    description = _clean_html_text(position_detail.get("description") or "")
    company_intro = _clean_html_text(company_detail.get("companyDescription") or "")
    industry = ",".join(
        part
        for part in [
            str(company_detail.get("industryNameLevel") or "").strip(),
            str(company_detail.get("industryLevel") or "").strip(),
            str(enriched.get("industry") or "").strip(),
        ]
        if part
    )
    if description:
        enriched["description"] = description
    if company_intro:
        enriched["company_intro"] = company_intro
    if industry:
        enriched["industry"] = industry
    enriched["salary_range"] = str(position_detail.get("salary") or enriched.get("salary_range") or "").strip()
    enriched["company_size"] = str(company_detail.get("companySize") or enriched.get("company_size") or "").strip()
    enriched["company_name"] = str(company_detail.get("companyName") or enriched.get("company_name") or "").strip()
    return normalize_job_dataset_row(enriched) or enriched


def _dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen_codes: set[str] = set()
    seen_fallback: set[tuple[str, str, str]] = set()
    for row in rows:
        job_code = str(row.get("job_code") or "").strip()
        fallback_key = (
            str(row.get("title") or "").strip().lower(),
            str(row.get("company_name") or "").strip().lower(),
            str(row.get("source_url") or "").strip().lower(),
        )
        if job_code and job_code in seen_codes:
            continue
        if fallback_key in seen_fallback:
            continue
        if job_code:
            seen_codes.add(job_code)
        seen_fallback.add(fallback_key)
        result.append({header: row.get(header, "") for header in HEADERS})
    return result


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in HEADERS})


def main() -> None:
    args = parse_args()
    dataset_rows = load_job_postings_dataset(args.dataset)
    base_unique_rows = _dedupe_rows(dataset_rows)
    dataset_meta = get_job_dataset_metadata(args.dataset)
    target_total = int(len(base_unique_rows) * args.target_multiplier)
    target_additional = max(target_total - len(base_unique_rows), 0)
    existing_codes = {str(row.get("job_code") or "").strip() for row in base_unique_rows}

    print(f"Base filtered rows: {len(dataset_rows)}")
    print(f"Base unique postings: {len(base_unique_rows)}")
    print(f"Target unique postings: {target_total}")
    print(f"Target additional unique postings: {target_additional}")

    city_codes = _extract_city_map()
    seed_cities = _choose_seed_cities(dataset_rows, city_codes, args.max_city_count)
    seed_keywords = _choose_seed_keywords(dataset_rows, args.max_keyword_count)
    print(f"Seed cities: {len(seed_cities)}")
    print(f"Seed keywords: {len(seed_keywords)}")

    crawled_rows: list[dict[str, Any]] = []
    query_index = 0
    total_queries = len(seed_cities) * len(seed_keywords)
    enough_candidates = False
    for city_name, city_code in seed_cities:
        for keyword in seed_keywords:
            query_index += 1
            rows = _fetch_list_rows(city_code, keyword, args.max_pages_per_query, args.sleep_seconds)
            if not rows:
                continue
            crawled_rows.extend(rows)
            deduped = _dedupe_rows(crawled_rows)
            fresh_candidate_count = sum(
                1 for row in deduped if str(row.get("job_code") or "").strip() not in existing_codes
            )
            print(
                f"[{query_index}/{total_queries}] {city_name} / {keyword}: "
                f"raw={len(rows)} accumulated={len(deduped)} fresh={fresh_candidate_count}"
            )
            if target_additional and fresh_candidate_count >= int(target_additional * 1.8):
                enough_candidates = True
                break
        if enough_candidates:
            break

    unique_candidates = _dedupe_rows(crawled_rows)
    fresh_candidates = [row for row in unique_candidates if str(row.get("job_code") or "").strip() not in existing_codes]
    print(f"Unique crawled rows: {len(unique_candidates)}")
    print(f"Fresh rows before detail fetch: {len(fresh_candidates)}")

    detailed_rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.detail_workers)) as executor:
        futures = {executor.submit(_fetch_detail_enrichment, row): row for row in fresh_candidates}
        for index, future in enumerate(as_completed(futures), start=1):
            try:
                detailed_rows.append(future.result())
            except Exception:
                detailed_rows.append(futures[future])
            if index % 200 == 0 or index == len(futures):
                print(f"Fetched details: {index}/{len(futures)}")

    cleaned_rows = filter_computer_related_rows(_dedupe_rows(detailed_rows))
    supplemental_rows = cleaned_rows[:target_additional] if target_additional else cleaned_rows
    merged_rows = _dedupe_rows(base_unique_rows + supplemental_rows)

    supplement_output = Path(args.supplement_output)
    merged_output = Path(args.merged_output)
    _write_csv(supplement_output, supplemental_rows)
    _write_csv(merged_output, merged_rows)

    print("Supplement crawl complete")
    print(f"- Base dataset raw rows: {dataset_meta['raw_row_count']}")
    print(f"- Base filtered rows: {len(dataset_rows)}")
    print(f"- Base unique postings: {len(base_unique_rows)}")
    print(f"- Supplemental usable rows: {len(supplemental_rows)}")
    print(f"- Merged usable rows: {len(merged_rows)}")
    print(f"- Supplemental output: {supplement_output}")
    print(f"- Merged output: {merged_output}")


if __name__ == "__main__":
    main()
