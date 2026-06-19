from ontology_studio.core.models import OntologyNode, OntologyRelationship, OntologySpec


def default_ontology(domain: str = "compliance") -> OntologySpec:
    if domain == "finance":
        return OntologySpec(
            domain="finance",
            nodes=[
                OntologyNode(
                    label="ETF",
                    description="상장지수펀드 상품",
                    key_property="ticker",
                    examples=["KODEX 200", "TIGER 미국S&P500"],
                ),
                OntologyNode(
                    label="Issuer",
                    description="ETF 운용사",
                    key_property="name",
                    examples=["삼성자산운용", "미래에셋자산운용"],
                ),
                OntologyNode(
                    label="AssetClass",
                    description="상품이 추종하는 자산군",
                    key_property="name",
                    examples=["주식", "채권", "원자재"],
                ),
                OntologyNode(
                    label="RiskFactor",
                    description="투자 리스크 요인",
                    key_property="name",
                    examples=["환율", "금리", "섹터 집중도"],
                ),
            ],
            relationships=[
                OntologyRelationship(
                    type="ISSUED_BY",
                    source="ETF",
                    target="Issuer",
                    description="ETF를 운용사가 발행하거나 운용한다.",
                ),
                OntologyRelationship(
                    type="TRACKS",
                    source="ETF",
                    target="AssetClass",
                    description="ETF가 특정 자산군이나 지수를 추종한다.",
                ),
                OntologyRelationship(
                    type="EXPOSED_TO",
                    source="ETF",
                    target="RiskFactor",
                    description="ETF가 특정 위험 요인에 노출된다.",
                ),
            ],
            constraints=["ETF.ticker must be unique", "Issuer.name must be unique"],
        )

    return OntologySpec(
        domain="compliance",
        nodes=[
            OntologyNode(
                label="Policy",
                description="법령, 사내 규정, 운영 정책 문서",
                key_property="policy_id",
                examples=["근로기준법", "개인정보 처리방침"],
            ),
            OntologyNode(
                label="Section",
                description="문서 내부의 장, 조, 항, 호",
                key_property="section_id",
                examples=["제12조", "2장 4항"],
            ),
            OntologyNode(
                label="Rule",
                description="실제로 판단에 쓰이는 규칙",
                key_property="rule_id",
                examples=["보존 기간 3년", "사전 동의 필요"],
            ),
            OntologyNode(
                label="Team",
                description="규정의 책임 부서",
                key_property="name",
                examples=["법무팀", "인사팀", "보안팀"],
            ),
            OntologyNode(
                label="Evidence",
                description="승인 문서, 로그, 계약서 같은 증빙",
                key_property="evidence_id",
                examples=["전자결재 문서", "접근 로그"],
            ),
        ],
        relationships=[
            OntologyRelationship(
                type="HAS_SECTION",
                source="Policy",
                target="Section",
                description="정책 문서가 조항을 포함한다.",
            ),
            OntologyRelationship(
                type="HAS_RULE",
                source="Section",
                target="Rule",
                description="조항에서 판단 규칙을 도출한다.",
            ),
            OntologyRelationship(
                type="OWNED_BY",
                source="Rule",
                target="Team",
                description="규칙의 운영 책임 부서를 연결한다.",
            ),
            OntologyRelationship(
                type="REQUIRES",
                source="Rule",
                target="Evidence",
                description="규칙 준수에 필요한 증빙을 연결한다.",
            ),
        ],
        constraints=["Policy.policy_id must be unique", "Rule.rule_id must be unique"],
    )
