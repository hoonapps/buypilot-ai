from specpilot_ai.core.models import Category, CheckStatus, CompatibilityCheck, ProductCandidate


def build_compatibility_checks(product: ProductCandidate) -> list[CompatibilityCheck]:
    if product.category == Category.laptop:
        return _laptop_checks(product)
    return _desktop_checks(product)


def compatibility_score(checks: list[CompatibilityCheck]) -> float:
    if not checks:
        return 70.0
    penalty = 0.0
    for check in checks:
        if check.status == CheckStatus.warning:
            penalty += 8.0
        elif check.status == CheckStatus.blocker:
            penalty += 28.0
    return max(35.0, 100.0 - penalty)


def compatibility_summary(checks: list[CompatibilityCheck]) -> str:
    blockers = [check for check in checks if check.status == CheckStatus.blocker]
    warnings = [check for check in checks if check.status == CheckStatus.warning]
    if blockers:
        return f"구매 전 차단 이슈 {len(blockers)}개를 반드시 해결해야 합니다."
    if warnings:
        return f"치명적 문제는 없지만 확인 경고 {len(warnings)}개가 있습니다."
    return "소켓, 전력, 공간, 업그레이드 기준에서 주요 호환성 문제가 없습니다."


def _desktop_checks(product: ProductCandidate) -> list[CompatibilityCheck]:
    specs = product.specs
    checks: list[CompatibilityCheck] = []
    socket_ok = specs.get("cpu_socket") == specs.get("motherboard_socket")
    checks.append(
        CompatibilityCheck(
            product_id=product.id,
            component="CPU/메인보드 소켓",
            status=CheckStatus.ok if socket_ok else CheckStatus.blocker,
            message=(
                f"{specs.get('cpu_socket')} CPU와 {specs.get('motherboard_socket')} 보드"
                if socket_ok
                else "CPU와 메인보드 소켓이 맞지 않습니다."
            ),
            evidence="CPU socket and motherboard socket fields",
        )
    )

    gpu = str(specs.get("gpu", ""))
    psu_watt = float(specs.get("psu_watt", 0))
    required_psu = _required_psu_watt(gpu)
    checks.append(
        CompatibilityCheck(
            product_id=product.id,
            component="파워 용량",
            status=CheckStatus.ok if psu_watt >= required_psu else CheckStatus.warning,
            message=f"{gpu} 기준 권장 {required_psu:.0f}W, 구성안은 {psu_watt:.0f}W입니다.",
            evidence="GPU class based PSU rule",
        )
    )

    gpu_clearance = float(specs.get("case_gpu_clearance_mm", 0))
    gpu_length = float(specs.get("gpu_length_mm", 0))
    clearance_margin = gpu_clearance - gpu_length
    checks.append(
        CompatibilityCheck(
            product_id=product.id,
            component="케이스 GPU 장착 공간",
            status=CheckStatus.ok if clearance_margin >= 25 else CheckStatus.warning,
            message=f"GPU 길이 여유 {clearance_margin:.0f}mm입니다.",
            evidence="case_gpu_clearance_mm - gpu_length_mm",
        )
    )

    cooler_margin = float(specs.get("case_cooler_clearance_mm", 0)) - float(
        specs.get("cooler_height_mm", 0)
    )
    checks.append(
        CompatibilityCheck(
            product_id=product.id,
            component="CPU 쿨러 높이",
            status=CheckStatus.ok if cooler_margin >= 8 else CheckStatus.warning,
            message=f"쿨러 높이 여유 {cooler_margin:.0f}mm입니다.",
            evidence="case_cooler_clearance_mm - cooler_height_mm",
        )
    )

    ram_gb = float(specs.get("ram_gb", 0))
    checks.append(
        CompatibilityCheck(
            product_id=product.id,
            component="메모리",
            status=CheckStatus.ok if ram_gb >= 32 else CheckStatus.warning,
            message=f"영상 편집/QHD 기준 권장 32GB, 구성안은 {ram_gb:.0f}GB입니다.",
            evidence="ram_gb workload rule",
        )
    )
    return checks


def _laptop_checks(product: ProductCandidate) -> list[CompatibilityCheck]:
    specs = product.specs
    checks: list[CompatibilityCheck] = []
    ram_gb = float(specs.get("ram_gb", 0))
    external_gpu = int(specs.get("external_gpu", 0))
    weight_kg = float(specs.get("weight_kg", 9))
    battery_wh = float(specs.get("battery_wh", 0))

    checks.append(
        CompatibilityCheck(
            product_id=product.id,
            component="RAM 용량",
            status=CheckStatus.ok if ram_gb >= 32 else CheckStatus.warning,
            message=f"크리에이터 작업 권장 32GB, 이 모델은 {ram_gb:.0f}GB입니다.",
            evidence="ram_gb workload rule",
        )
    )
    checks.append(
        CompatibilityCheck(
            product_id=product.id,
            component="GPU 가속",
            status=CheckStatus.ok if external_gpu else CheckStatus.warning,
            message="외장 GPU가 있어 편집/렌더링 가속에 유리합니다."
            if external_gpu
            else "외장 GPU가 없어 GPU 가속 작업은 제한적입니다.",
            evidence="external_gpu flag",
        )
    )
    checks.append(
        CompatibilityCheck(
            product_id=product.id,
            component="휴대성",
            status=CheckStatus.ok if weight_kg <= 1.8 else CheckStatus.warning,
            message=f"무게 {weight_kg:.2f}kg입니다.",
            evidence="weight_kg threshold",
        )
    )
    checks.append(
        CompatibilityCheck(
            product_id=product.id,
            component="배터리",
            status=CheckStatus.ok if battery_wh >= 70 else CheckStatus.warning,
            message=f"배터리 {battery_wh:.0f}Wh입니다.",
            evidence="battery_wh threshold",
        )
    )
    return checks


def _required_psu_watt(gpu: str) -> float:
    if "4090" in gpu:
        return 1000.0
    if "4080" in gpu:
        return 850.0
    if "4070" in gpu:
        return 750.0
    if "4060" in gpu or "7600" in gpu:
        return 650.0
    return 550.0
