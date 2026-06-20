from datetime import UTC, datetime

from specpilot_ai.core.models import (
    Category,
    CheckStatus,
    PublicSetupCompatibilityKit,
    SetupCompatibilityCheck,
    SetupCompatibilityRequest,
    SpecRiskScannerRequest,
)


def build_public_setup_compatibility_kit(
    request: SetupCompatibilityRequest,
    generated_at: datetime | None = None,
) -> PublicSetupCompatibilityKit:
    generated_at = generated_at or datetime.now(UTC)
    checks = (
        _desktop_checks(request)
        if request.category == Category.desktop_pc
        else _laptop_checks(request)
    )
    blocker_count = sum(1 for check in checks if check.status == CheckStatus.blocker)
    warning_count = sum(1 for check in checks if check.status == CheckStatus.warning)
    compatibility_score = _compatibility_score(blocker_count, warning_count, len(checks))
    verdict = _verdict(blocker_count, warning_count)
    scanner_prefill = _scanner_prefill(request)
    return PublicSetupCompatibilityKit(
        generated_at=generated_at.isoformat(),
        category=request.category,
        compatibility_score=compatibility_score,
        verdict=verdict,
        headline=_headline(request, verdict),
        summary=_summary(request, blocker_count, warning_count, compatibility_score),
        blocker_count=blocker_count,
        warning_count=warning_count,
        checks=checks,
        recommended_changes=_recommended_changes(request, checks),
        scanner_prefill=scanner_prefill,
        analysis_prefill=_analysis_prefill(request, scanner_prefill, verdict),
        share_copy=_share_copy(request, compatibility_score, checks),
        next_actions=_next_actions(verdict, checks),
    )


def _desktop_checks(request: SetupCompatibilityRequest) -> list[SetupCompatibilityCheck]:
    return [
        _gpu_monitor_check(request),
        _cpu_gpu_balance_check(request),
        _ram_check(request),
        _storage_check(request),
        _psu_check(request),
        _form_factor_check(request),
    ]


def _laptop_checks(request: SetupCompatibilityRequest) -> list[SetupCompatibilityCheck]:
    return [
        _gpu_monitor_check(request),
        _ram_check(request),
        _storage_check(request),
        _laptop_weight_check(request),
        _laptop_battery_check(request),
    ]


def _gpu_monitor_check(request: SetupCompatibilityRequest) -> SetupCompatibilityCheck:
    resolution = _resolution(request.monitor_resolution)
    gpu_tier = _gpu_tier(request.gpu)
    if request.category == Category.laptop and _needs_gpu_acceleration(request) and gpu_tier == 0:
        return _check(
            "gpu_monitor",
            "GPU/화면 목적",
            CheckStatus.blocker,
            f"{request.gpu or '외장 GPU 미입력'} / {resolution}",
            "영상 편집, 3D, QHD 게임 목적이면 외장 GPU 모델을 먼저 확인하세요.",
            "GPU 가속이 필요한 작업에서 체감 성능이 크게 떨어질 수 있습니다.",
        )
    if resolution == "4k" and gpu_tier < 4:
        return _check(
            "gpu_monitor",
            "GPU/모니터 해상도",
            CheckStatus.warning,
            f"{request.gpu or 'GPU 미입력'} / 4K",
            "4K 게임·편집이면 RTX 4070급 이상 또는 목적 축소를 검토하세요.",
            "해상도 대비 GPU 여유가 작아 프레임이나 렌더 시간이 흔들릴 수 있습니다.",
        )
    if resolution == "qhd" and gpu_tier < 2:
        return _check(
            "gpu_monitor",
            "GPU/모니터 해상도",
            CheckStatus.warning,
            f"{request.gpu or 'GPU 미입력'} / QHD",
            "QHD 게임이나 영상 편집이면 RTX 4060급 이상을 기준으로 다시 보세요.",
            "QHD 기준 성능 여유가 부족할 수 있습니다.",
        )
    if resolution == "fhd" and gpu_tier >= 5:
        return _check(
            "gpu_monitor",
            "GPU/모니터 해상도",
            CheckStatus.warning,
            f"{request.gpu} / FHD",
            "FHD만 쓴다면 GPU 예산을 낮추거나 QHD 모니터 예산을 함께 잡으세요.",
            "현재 조합은 성능보다 예산 과투자 가능성이 큽니다.",
        )
    return _check(
        "gpu_monitor",
        "GPU/모니터 해상도",
        CheckStatus.ok,
        f"{request.gpu or 'GPU 미입력'} / {resolution.upper()}",
        "목적과 해상도 기준의 큰 병목은 보이지 않습니다.",
        "후보별 벤치마크와 실제 가격으로 최종 확인하세요.",
    )


def _cpu_gpu_balance_check(request: SetupCompatibilityRequest) -> SetupCompatibilityCheck:
    cpu_tier = _cpu_tier(request.cpu)
    gpu_tier = _gpu_tier(request.gpu)
    if gpu_tier >= 4 and cpu_tier <= 1:
        return _check(
            "cpu_gpu_balance",
            "CPU/GPU 균형",
            CheckStatus.warning,
            f"{request.cpu or 'CPU 미입력'} / {request.gpu}",
            "상위 GPU에는 Ryzen 5/i5 이상, 작업용이면 Ryzen 7/i7 이상을 권장합니다.",
            "CPU가 낮으면 고가 GPU 성능을 다 쓰지 못할 수 있습니다.",
        )
    if _needs_creator_memory(request) and cpu_tier == 0:
        return _check(
            "cpu_gpu_balance",
            "CPU/GPU 균형",
            CheckStatus.warning,
            request.cpu or "CPU 미입력",
            "영상 편집/개발 목적이면 CPU 모델명과 세대를 명확히 확인하세요.",
            "CPU 정보가 불명확하면 후보 비교의 성능 판단이 약해집니다.",
        )
    return _check(
        "cpu_gpu_balance",
        "CPU/GPU 균형",
        CheckStatus.ok,
        f"{request.cpu or 'CPU 미입력'} / {request.gpu or 'GPU 미입력'}",
        "큰 CPU/GPU 불균형 신호는 없습니다.",
        "실사용 목적별 벤치마크로 최종 확인하세요.",
    )


def _ram_check(request: SetupCompatibilityRequest) -> SetupCompatibilityCheck:
    ram = request.ram_gb or 0
    required = 32 if _needs_creator_memory(request) else 16
    if ram == 0:
        return _check(
            "ram",
            "RAM 용량",
            CheckStatus.warning,
            "RAM 미입력",
            f"목적 기준 최소 {required}GB를 장바구니 옵션에서 확인하세요.",
            "메모리 옵션 누락은 구매 후 업그레이드 비용으로 이어질 수 있습니다.",
        )
    if ram < max(16, required // 2):
        return _check(
            "ram",
            "RAM 용량",
            CheckStatus.blocker,
            f"{ram}GB",
            f"현재 목적이면 {required}GB 이상 후보로 바꾸세요.",
            "메모리 부족은 편집, 게임, 개발 작업에서 즉시 병목이 됩니다.",
        )
    if ram < required:
        return _check(
            "ram",
            "RAM 용량",
            CheckStatus.warning,
            f"{ram}GB",
            f"{required}GB 옵션 또는 업그레이드 가능 여부를 확인하세요.",
            "당장은 가능해도 장기 사용 여유가 작습니다.",
        )
    return _check(
        "ram",
        "RAM 용량",
        CheckStatus.ok,
        f"{ram}GB",
        "목적 기준 RAM 용량은 충분합니다.",
        "듀얼 채널 구성과 업그레이드 슬롯만 추가 확인하세요.",
    )


def _storage_check(request: SetupCompatibilityRequest) -> SetupCompatibilityCheck:
    storage = request.storage_gb or 0
    required = 1000 if _needs_creator_memory(request) else 512
    if storage == 0:
        return _check(
            "storage",
            "저장장치",
            CheckStatus.warning,
            "SSD 미입력",
            f"목적 기준 SSD {required}GB 이상인지 확인하세요.",
            "저장장치 옵션 누락은 결제 후 추가 비용으로 이어질 수 있습니다.",
        )
    if storage < 256:
        return _check(
            "storage",
            "저장장치",
            CheckStatus.blocker,
            f"{storage}GB",
            "최소 512GB 이상, 작업용이면 1TB 이상으로 바꾸세요.",
            "OS와 필수 앱 설치 후 실사용 공간이 부족합니다.",
        )
    if storage < required:
        return _check(
            "storage",
            "저장장치",
            CheckStatus.warning,
            f"{storage}GB",
            f"작업 파일까지 고려해 {required}GB 이상을 권장합니다.",
            "외장 저장장치나 추가 SSD 비용이 필요할 수 있습니다.",
        )
    return _check(
        "storage",
        "저장장치",
        CheckStatus.ok,
        f"{storage}GB",
        "목적 기준 저장장치 용량은 무난합니다.",
        "NVMe 여부와 추가 슬롯을 확인하세요.",
    )


def _psu_check(request: SetupCompatibilityRequest) -> SetupCompatibilityCheck:
    required = _required_psu_watt(request.gpu)
    psu = request.psu_watt or 0
    if psu == 0:
        return _check(
            "psu",
            "파워 용량",
            CheckStatus.warning,
            "파워 용량 미입력",
            f"{request.gpu or 'GPU'} 기준 권장 {required}W 이상인지 확인하세요.",
            "파워 정보가 없으면 완제품 옵션명과 상세 페이지 검수가 필요합니다.",
        )
    if psu < int(required * 0.9):
        return _check(
            "psu",
            "파워 용량",
            CheckStatus.blocker,
            f"{psu}W / 권장 {required}W",
            f"{required}W 이상 정격 파워 후보로 바꾸세요.",
            "전력 여유 부족은 안정성, 소음, 업그레이드 여지를 모두 줄입니다.",
        )
    if psu < required:
        return _check(
            "psu",
            "파워 용량",
            CheckStatus.warning,
            f"{psu}W / 권장 {required}W",
            "권장 용량보다 낮아 판매자에게 파워 모델명과 정격 출력을 확인하세요.",
            "고부하 작업에서 안정성 여유가 작습니다.",
        )
    return _check(
        "psu",
        "파워 용량",
        CheckStatus.ok,
        f"{psu}W / 권장 {required}W",
        "GPU 기준 파워 용량은 충분합니다.",
        "정격 인증, 제조사, 보증 기간을 추가 확인하세요.",
    )


def _form_factor_check(request: SetupCompatibilityRequest) -> SetupCompatibilityCheck:
    form = request.form_factor.strip().lower() or "폼팩터 미입력"
    gpu_tier = _gpu_tier(request.gpu)
    if any(token in form for token in ["slim", "초슬림", "미니", "mini", "itx"]) and gpu_tier >= 4:
        status = CheckStatus.blocker if "slim" in form or "초슬림" in form else CheckStatus.warning
        return _check(
            "form_factor",
            "케이스/폼팩터",
            status,
            f"{form} / {request.gpu}",
            "고성능 GPU는 길이, 두께, 쿨링 여유를 상세 페이지에서 확인하세요.",
            "작은 케이스는 발열, 소음, 장착 간섭 리스크가 큽니다.",
        )
    return _check(
        "form_factor",
        "케이스/폼팩터",
        CheckStatus.ok,
        form,
        "폼팩터 기준의 명확한 장착 차단 신호는 없습니다.",
        "GPU 길이와 CPU 쿨러 높이는 결제 전 상세 스펙으로 확인하세요.",
    )


def _laptop_weight_check(request: SetupCompatibilityRequest) -> SetupCompatibilityCheck:
    weight = request.weight_kg or 0
    portable = "portable" in request.purpose.lower() or "휴대" in request.purpose
    if not weight:
        return _check(
            "weight",
            "노트북 무게",
            CheckStatus.warning,
            "무게 미입력",
            "휴대 목적이면 kg 단위 무게를 반드시 확인하세요.",
            "무게 정보가 없으면 휴대성 판단이 어렵습니다.",
        )
    if portable and weight > 2.0:
        return _check(
            "weight",
            "노트북 무게",
            CheckStatus.warning,
            f"{weight:.2f}kg",
            "출장/통학 휴대가 많다면 1.8kg 안팎 후보와 비교하세요.",
            "무게가 구매 만족도와 사용 빈도에 직접 영향을 줍니다.",
        )
    return _check(
        "weight",
        "노트북 무게",
        CheckStatus.ok,
        f"{weight:.2f}kg",
        "목적 기준 무게는 큰 문제가 없어 보입니다.",
        "충전기 무게와 배터리 사용 시간을 함께 확인하세요.",
    )


def _laptop_battery_check(request: SetupCompatibilityRequest) -> SetupCompatibilityCheck:
    battery = request.battery_wh or 0
    if not battery:
        return _check(
            "battery",
            "배터리",
            CheckStatus.warning,
            "배터리 미입력",
            "휴대 목적이면 배터리 Wh와 실제 사용 시간을 확인하세요.",
            "배터리 정보가 없으면 외부 작업 지속 시간을 판단하기 어렵습니다.",
        )
    if battery < 60 and ("portable" in request.purpose.lower() or "휴대" in request.purpose):
        return _check(
            "battery",
            "배터리",
            CheckStatus.warning,
            f"{battery}Wh",
            "휴대 작업이면 70Wh 안팎 후보와 비교하세요.",
            "외부 작업 시간이 짧을 수 있습니다.",
        )
    return _check(
        "battery",
        "배터리",
        CheckStatus.ok,
        f"{battery}Wh",
        "목적 기준 배터리 용량은 무난합니다.",
        "GPU 사용 시 실제 지속 시간은 별도 리뷰 근거로 확인하세요.",
    )


def _check(
    check_id: str,
    label: str,
    status: CheckStatus,
    observed: str,
    recommendation: str,
    impact: str,
) -> SetupCompatibilityCheck:
    return SetupCompatibilityCheck(
        check_id=check_id,
        label=label,
        status=status,
        observed=observed,
        recommendation=recommendation,
        impact=impact,
    )


def _compatibility_score(blocker_count: int, warning_count: int, total_count: int) -> float:
    if total_count == 0:
        return 70.0
    return round(max(10.0, min(100.0, 100 - blocker_count * 24 - warning_count * 9)), 1)


def _verdict(blocker_count: int, warning_count: int) -> str:
    if blocker_count:
        return "hold"
    if warning_count:
        return "verify"
    return "ready"


def _headline(request: SetupCompatibilityRequest, verdict: str) -> str:
    label = "노트북" if request.category == Category.laptop else "데스크톱 PC"
    if verdict == "hold":
        return f"{label} 세팅에 결제 전 차단 리스크가 있습니다."
    if verdict == "verify":
        return f"{label} 세팅은 가능하지만 확인할 병목이 남아 있습니다."
    return f"{label} 세팅은 목적 기준 큰 호환성 문제가 없습니다."


def _summary(
    request: SetupCompatibilityRequest,
    blocker_count: int,
    warning_count: int,
    score: float,
) -> str:
    label = "노트북" if request.category == Category.laptop else "데스크톱 PC"
    return (
        f"{label} 조합을 {request.purpose} 목적과 {request.budget_krw:,}원 예산 기준으로 점검했습니다. "
        f"호환성 점수 {score}점, blocker {blocker_count}개, warning {warning_count}개입니다."
    )


def _recommended_changes(
    request: SetupCompatibilityRequest,
    checks: list[SetupCompatibilityCheck],
) -> list[str]:
    changes = [
        check.recommendation
        for check in checks
        if check.status != CheckStatus.ok
    ]
    if not changes:
        changes.append("현재 조합은 후보 비교와 가격 타이밍 확인으로 넘어가도 됩니다.")
    if request.category == Category.desktop_pc and not request.psu_watt:
        changes.append("완제품 상세 페이지에서 파워 제조사, 정격 출력, 보증 기간을 캡처하세요.")
    return changes[:5]


def _scanner_prefill(request: SetupCompatibilityRequest) -> SpecRiskScannerRequest:
    option_parts = [
        request.cpu,
        request.gpu,
        f"RAM {request.ram_gb}GB" if request.ram_gb else "",
        f"SSD {request.storage_gb}GB" if request.storage_gb else "",
        f"PSU {request.psu_watt}W" if request.psu_watt else "",
        request.form_factor,
    ]
    return SpecRiskScannerRequest(
        category=request.category,
        product_title=_setup_title(request),
        option_text=" / ".join(part for part in option_parts if part),
        cart_total_krw=None,
        budget_krw=request.budget_krw,
        expected_cpu=request.cpu,
        expected_gpu=request.gpu,
        expected_ram_gb=request.ram_gb,
        expected_storage_gb=request.storage_gb,
        expected_os="",
        evidence_text=(
            f"모니터 {request.monitor_resolution}, 목적 {request.purpose}, "
            "세팅 호환성 키트 기반 prefill"
        ),
        source="setup_compatibility",
    )


def _analysis_prefill(
    request: SetupCompatibilityRequest,
    scanner_prefill: SpecRiskScannerRequest,
    verdict: str,
) -> str:
    return (
        f"{_setup_title(request)} 조합을 {request.budget_krw:,}원 예산으로 사도 되는지 봐줘. "
        f"목적은 {request.purpose}, 판정은 {verdict}야. "
        f"CPU {scanner_prefill.expected_cpu or '미입력'}, GPU {scanner_prefill.expected_gpu or '미입력'}, "
        f"RAM {scanner_prefill.expected_ram_gb or '미입력'}GB, SSD {scanner_prefill.expected_storage_gb or '미입력'}GB, "
        f"모니터 {request.monitor_resolution}, 파워 {request.psu_watt or '미입력'}W 기준으로 "
        "호환성, 병목, 과투자, 대체 후보, 결제 전 검수까지 같이 판단해줘."
    )


def _share_copy(
    request: SetupCompatibilityRequest,
    score: float,
    checks: list[SetupCompatibilityCheck],
) -> str:
    lines = [
        "SpecPilot AI 세팅 호환성 체크",
        f"- 조합: {_setup_title(request)}",
        f"- 목적/예산: {request.purpose} / {request.budget_krw:,}원",
        f"- 호환성 점수: {score}점",
    ]
    lines.extend(
        f"- {check.label}: {check.status.value} / {check.observed}"
        for check in checks[:5]
    )
    lines.append("이 조합으로 결제해도 되는지 병목과 대체 후보 의견 부탁드립니다.")
    return "\n".join(lines)


def _next_actions(verdict: str, checks: list[SetupCompatibilityCheck]) -> list[str]:
    actions = [
        "호환성 결과를 장바구니 옵션명과 대조해 실제 판매 페이지 사양이 같은지 확인하세요.",
        "warning 항목은 판매자 질문이나 상세 페이지 캡처로 먼저 증거를 남기세요.",
        "분석 리포트로 같은 예산대 대체 후보와 가격 타이밍을 같이 비교하세요.",
    ]
    if verdict == "hold":
        actions.insert(0, "blocker가 남아 있으면 가격이 좋아도 바로 결제하지 마세요.")
    return actions


def _setup_title(request: SetupCompatibilityRequest) -> str:
    label = "노트북" if request.category == Category.laptop else "데스크톱 PC"
    parts = [request.cpu, request.gpu]
    return f"{label} 세팅 " + " / ".join(part for part in parts if part)


def _required_psu_watt(gpu: str) -> int:
    tier = _gpu_tier(gpu)
    if tier >= 6:
        return 1000
    if tier >= 5:
        return 850
    if tier >= 4:
        return 750
    if tier >= 2:
        return 650
    return 550


def _gpu_tier(gpu: str) -> int:
    normalized = gpu.lower().replace(" ", "")
    if any(token in normalized for token in ["4090", "5090"]):
        return 6
    if any(token in normalized for token in ["4080", "5080", "7900xtx"]):
        return 5
    if any(token in normalized for token in ["4070", "5070", "7800xt"]):
        return 4
    if any(token in normalized for token in ["4060ti", "3070", "7700xt"]):
        return 3
    if any(token in normalized for token in ["4060", "3060", "7600"]):
        return 2
    if any(token in normalized for token in ["iris", "radeon", "arc", "내장", "integrated"]):
        return 1
    return 0


def _cpu_tier(cpu: str) -> int:
    normalized = cpu.lower().replace(" ", "")
    if any(token in normalized for token in ["ryzen9", "i9", "ultra9", "m3max", "m4max"]):
        return 4
    if any(token in normalized for token in ["ryzen7", "i7", "ultra7", "m3pro", "m4pro"]):
        return 3
    if any(token in normalized for token in ["ryzen5", "i5", "ultra5", "m3", "m4"]):
        return 2
    if any(token in normalized for token in ["ryzen3", "i3"]):
        return 1
    return 0


def _resolution(value: str) -> str:
    normalized = value.lower()
    if "4k" in normalized or "uhd" in normalized or "2160" in normalized:
        return "4k"
    if "qhd" in normalized or "1440" in normalized or "2k" in normalized:
        return "qhd"
    return "fhd"


def _needs_creator_memory(request: SetupCompatibilityRequest) -> bool:
    normalized = request.purpose.lower()
    return any(token in normalized for token in ["creator", "video", "편집", "qhd", "개발", "3d"])


def _needs_gpu_acceleration(request: SetupCompatibilityRequest) -> bool:
    normalized = request.purpose.lower()
    return any(token in normalized for token in ["creator", "video", "편집", "qhd", "gaming", "게임", "3d"])
