# S11：Gateway 在 Fargate 上的兩個身分各能做什麼（E123 定案 2 的驗收畫面）
#   任務角色：Gateway 程式用（三張表、向 STS 要 OpenAI 用的身分證明）
#   執行角色：ECS 平台用（拉映像、寫日誌、讀三個 SSM 參數）
# 每一條權限印一列：Sid、動作、資源、條件；帳號 ID 一律換成 <account-id>
# Resource 是 "*" 的只有 AWS 規定不能指定資源的兩個動作，而且都有理由（見 infra/persistent/ecs_roles.tf）
# 用法（repo 根目錄、aws login 之後）：.\scripts\show_gateway_roles.ps1

function Hide-AccountId($text) { $text -replace '\d{12}', '<account-id>' }

foreach ($role in @("llm-gateway-task", "llm-gateway-task-execution")) {
  Write-Output "== $role =="
  $document = aws iam get-role-policy --role-name $role --policy-name $role `
    --query "PolicyDocument" --output json | Out-String | ConvertFrom-Json
  $rows = foreach ($statement in @($document.Statement)) {
    $condition = ""
    if ($statement.Condition) {
      $condition = ($statement.Condition.PSObject.Properties | ForEach-Object {
        $test = $_.Name
        $_.Value.PSObject.Properties | ForEach-Object { "$test $($_.Name) = $(@($_.Value) -join ', ')" }
      }) -join "`n"
    }
    [pscustomobject]@{
      Sid       = $statement.Sid
      Action    = (@($statement.Action) -join "`n")
      Resource  = Hide-AccountId (@($statement.Resource) -join "`n")
      Condition = $condition
    }
  }
  $rows | Format-List
}
