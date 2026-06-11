def fetch_contributions(repository: str, token: str) -> list[UserContributionCounts]:
    owner, name = repository.split("/", maxsplit=1)
    client = create_client(token)

    contributions: dict[str, UserContributionCounts] = {}

    combined_query = gql("""
    query($owner: String!, $name: String!, $issueCursor: String, $prCursor: String) {
        repository(owner: $owner, name: $name) {
            issues(first: 100, after: $issueCursor, states: [OPEN, CLOSED]) {
                pageInfo { hasNextPage endCursor }
                nodes {
                    author { login }
                    labels(first: 10) { nodes { name } }
                }
            }
            pullRequests(first: 100, after: $prCursor, states: [MERGED]) {
                pageInfo { hasNextPage endCursor }
                nodes {
                    author { login }
                    labels(first: 10) { nodes { name } }
                }
            }
        }
    }
    """)

    issue_cursor: str | None = None
    pr_cursor: str | None = None
    fetch_issues = True
    fetch_prs = True

    while fetch_issues or fetch_prs:
        variables: dict = {"owner": owner, "name": name}
        if fetch_issues:
            variables["issueCursor"] = issue_cursor
        if fetch_prs:
            variables["prCursor"] = pr_cursor

        with client as session:
            result = session.execute(combined_query, variable_values=variables)

        repo = result["repository"]

        # 이슈 처리
        if fetch_issues:
            issues = repo["issues"]
            for node in issues["nodes"]:
                if not node["author"]:
                    continue
                user = node["author"]["login"]
                labels = [l["name"].lower() for l in node["labels"]["nodes"]]
                if user not in contributions:
                    contributions[user] = UserContributionCounts(user=user)
                if "documentation" in labels:
                    contributions[user].doc_issue_count += 1
                elif "bug" in labels or "enhancement" in labels:
                    contributions[user].feature_bug_issue_count += 1

            if issues["pageInfo"]["hasNextPage"]:
                issue_cursor = issues["pageInfo"]["endCursor"]
            else:
                fetch_issues = False

        # PR 처리
        if fetch_prs:
            prs = repo["pullRequests"]
            for node in prs["nodes"]:
                if not node["author"]:
                    continue
                user = node["author"]["login"]
                labels = [l["name"].lower() for l in node["labels"]["nodes"]]
                if user not in contributions:
                    contributions[user] = UserContributionCounts(user=user)
                if "documentation" in labels:
                    contributions[user].doc_pr_count += 1
                elif "typo" in labels:
                    contributions[user].typo_pr_count += 1
                elif "bug" in labels or "enhancement" in labels:
                    contributions[user].feature_bug_pr_count += 1

            if prs["pageInfo"]["hasNextPage"]:
                pr_cursor = prs["pageInfo"]["endCursor"]
            else:
                fetch_prs = False

    return list(contributions.values())