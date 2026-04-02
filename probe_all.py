#!/usr/bin/env python3
"""Probe all discovered endpoints from JS analysis (files 1-80)."""
import boto3, requests, json, sys
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

session = boto3.Session()
creds = session.get_credentials().get_frozen_credentials()

def sigv4(method, url, region="us-east-1", service="execute-api", body=None):
    headers = {"Content-Type": "application/json"}
    req = AWSRequest(method=method, url=url, headers=headers, data=body or "")
    SigV4Auth(creds, service, region).add_auth(req)
    try:
        r = requests.request(method, url, headers=dict(req.headers), data=body or "", timeout=10)
        return r.status_code, r.text[:200]
    except Exception as e:
        return 0, str(e)[:100]

def plain(method, url, body=None, headers=None):
    try:
        h = {"Content-Type": "application/json"}
        if headers: h.update(headers)
        r = requests.request(method, url, headers=h, data=body or "", timeout=10)
        return r.status_code, r.text[:200]
    except Exception as e:
        return 0, str(e)[:100]

def test(label, method, url, mode="plain", region="us-east-1", service="execute-api", body=None, headers=None):
    if mode == "sigv4":
        code, text = sigv4(method, url, region, service, body)
    else:
        code, text = plain(method, url, body, headers)
    flag = " <<<" if code in (200, 201, 204) else ""
    print(f"[{code}] {method:6} {url[:120]}{flag}")
    if code in (200, 201, 204):
        print(f"        RESPONSE: {text}")

print("=" * 80)
print("=== API GATEWAY ENDPOINTS (SigV4) ===")
print("=" * 80)

# GNS App (file 9) - no auth in client code
for ep in [
    ("POST", "https://qmilj330s1.execute-api.us-west-2.amazonaws.com/dev", '{}'),
    ("POST", "https://qmilj330s1.execute-api.us-west-2.amazonaws.com/dev/accept", '{}'),
    ("POST", "https://qmilj330s1.execute-api.us-west-2.amazonaws.com/dev/reject", '{}'),
]:
    test("GNS", ep[0], ep[1], "sigv4", "us-west-2", body=ep[2])
    test("GNS-noauth", ep[0], ep[1], body=ep[2])

# GNS AppSync
test("GNS-AppSync", "POST", "https://kn5mu4kxp5dlzlrthduvzsp6ue.appsync-api.us-west-2.amazonaws.com/graphql",
     "sigv4", "us-west-2", "appsync", '{"query":"{ __schema { types { name } } }"}')

# 360eye (file 9)
test("360eye", "GET", "https://iyzvui9yrj.execute-api.us-east-1.amazonaws.com/prod", "sigv4")
test("360eye", "POST", "https://iyzvui9yrj.execute-api.us-east-1.amazonaws.com/prod", "sigv4", body='{}')
test("360eye-noauth", "GET", "https://iyzvui9yrj.execute-api.us-east-1.amazonaws.com/prod")

# Frontierhealthstatus (file 12)
test("frontier", "POST", "https://2yxj2z1v96.execute-api.us-west-2.amazonaws.com/alpha/v1/availability",
     "sigv4", "us-west-2", body='{}')

# Pricing Calculator (files 47-50 area)
test("pricecalc-graphql", "POST", "https://7bena91p37.execute-api.us-west-2.amazonaws.com/Prod/v1/graphql",
     "sigv4", "us-west-2", body='{"query":"{ __schema { types { name } } }"}')
test("pricecalc-stats-g", "POST", "https://3ni9bn7qlg.execute-api.us-west-2.amazonaws.com/Prod/stats/",
     "sigv4", "us-west-2", body='{}')
test("pricecalc-stats-b", "POST", "https://f5rys6urv6.execute-api.us-west-2.amazonaws.com/Prod/stats/",
     "sigv4", "us-west-2", body='{}')
test("pricecalc-mon", "POST", "https://mpvu3z0j51.execute-api.us-west-2.amazonaws.com/gamma/pec/monitoring/logging",
     "sigv4", "us-west-2", body='{}')

# Buckle (file 35 area)
test("buckle", "GET", "https://9mk5amthvb.execute-api.us-east-1.amazonaws.com/alpha/business/DEFAULT/region/NA/constraints", "sigv4")

# AppStream redirect / Brass API
test("brass-prod", "GET", "https://z2a2y5j969.execute-api.us-west-2.amazonaws.com/us-west-2", "sigv4", "us-west-2")
test("brass-beta", "GET", "https://98dbvmrln4.execute-api.us-west-2.amazonaws.com/us-west-2", "sigv4", "us-west-2")

# Node-exceptions logging
for ep in [
    "https://d16ymv4dd6.execute-api.us-east-1.amazonaws.com/prod/v1/log",
    "https://om50h44i04.execute-api.eu-west-1.amazonaws.com/prod/v1/log",
    "https://il4i39ve28.execute-api.us-east-1.amazonaws.com/prod/v1/log",
]:
    test("node-exc", "POST", ep, "sigv4", ep.split(".execute-api.")[1].split(".")[0], body='{"test":true}')

# JAM Lambda invoke (file 54)
test("jam-invoke", "POST", "https://msukbkfcl0.execute-api.us-east-1.amazonaws.com/beta/invoke", "sigv4", body='{}')

# ASIN Central logging
test("asin-log-prod", "POST", "https://u831naskbb.execute-api.us-east-1.amazonaws.com/prod/v1/log", "sigv4", body='{}')
test("asin-log-beta", "POST", "https://9zvb2n86n1.execute-api.us-west-2.amazonaws.com/prod/v1/log", "sigv4", "us-west-2", body='{}')

# Industry GCR AppSync
test("gcr-appsync", "POST", "https://zkf2bwawyjfe7eefanftj4erza.appsync-api.us-west-2.amazonaws.com/graphql",
     "sigv4", "us-west-2", "appsync", '{"query":"{ __schema { types { name } } }"}')

print("\n" + "=" * 80)
print("=== UNICORN AUCTIONS (no auth / raw userID auth) ===")
print("=" * 80)

for env in ["main", "prod", "staging", "moniami", "gbiagini"]:
    base = f"https://api.{env}.unicorn-auctions.wwco.aws.dev"
    test(f"unicorn-{env}", "POST", f"{base}/init", body='{"email":"probe@test.com"}')
    test(f"unicorn-{env}", "GET", f"{base}/auctions")
    test(f"unicorn-{env}", "GET", f"{base}/users")
    test(f"unicorn-{env}", "GET", f"{base}/users?userID=test")
    test(f"unicorn-{env}", "GET", f"{base}/items/1")

print("\n" + "=" * 80)
print("=== CURATOR / NICO (REST APIs) ===")
print("=" * 80)

for env, base in [
    ("dev", "https://api.dev.nico.proserve.aws.dev"),
    ("uat", "https://api.uat.nico.proserve.aws.dev"),
    ("prevdev", "https://api.prevdev.nico.proserve.aws.dev"),
    ("uat1", "https://api.uat1.curator.proserve.aws.dev"),
]:
    for path in ["/GetUserDetails", "/ListProjects", "/ListThreads?sourceId=Curator"]:
        test(f"nico-{env}", "GET", f"{base}{path}")
    test(f"nico-{env}", "POST", f"{base}/SendQuery", body='{"userQuery":"hello","threadId":"test","sourceId":"Curator"}')
    test(f"nico-{env}", "POST", f"{base}/v1", body='{"query":"hello"}')
    test(f"nico-{env}", "POST", f"{base}/v2", body='{"query":"hello"}')

print("\n" + "=" * 80)
print("=== MULTI-AGENT TOOLKIT ===")
print("=" * 80)

for env in ["beta", "gamma", "release"]:
    base = f"https://api.{env}.multi-agent-toolkit.proserve.aws.dev"
    test(f"mat-{env}", "GET", f"{base}/gateways")
    test(f"mat-{env}", "GET", f"{base}/capability-providers")
    test(f"mat-{env}", "GET", f"{base}/policies")

print("\n" + "=" * 80)
print("=== OSDU ENVIRONMENTS ===")
print("=" * 80)

for env in ["amergp1.amsdevedi.ams.dev.osdu.aws", "edi-upgrade2.amsdevedi.ams.dev.osdu.aws"]:
    base = f"https://{env}"
    test(f"osdu-{env[:8]}", "GET", f"{base}/api/schema-service/v1/schema")
    test(f"osdu-{env[:8]}", "GET", f"{base}/api/storage/v2/records")
    test(f"osdu-{env[:8]}", "GET", f"{base}/api/entitlements/v2/groups")
    test(f"osdu-{env[:8]}", "GET", f"{base}/api/v2/secrets")

print("\n" + "=" * 80)
print("=== FOODLENS ===")
print("=" * 80)

test("foodlens-config", "GET", "https://app.foodlens.pace.aws.dev/aws-exports.json")
test("foodlens-api", "POST", "https://d3fzsftrna1o97.cloudfront.net/fetchImage",
     body='{"productCode":"5000159484695","language":"english"}')
test("foodlens-api", "GET", "https://d3fzsftrna1o97.cloudfront.net/fetchIngredients/5000159484695/english")

print("\n" + "=" * 80)
print("=== S3 BUCKETS (public listing test) ===")
print("=" * 80)

for bucket in [
    "https://mcloud-production.s3.amazonaws.com",
    "https://aws-jam-challenge-resources.s3.amazonaws.com",
    "https://aws-jam-docs.s3-us-west-2.amazonaws.com",
    "https://osdu-artifacts.s3.us-east-1.amazonaws.com",
    "https://spot-bid-advisor.s3.amazonaws.com",
    "https://s3.us-west-2.amazonaws.com/pipeline-s3-bluescapepublicassetsbucket-1pxahw3j82g0v",
    "https://s3.us-west-2.amazonaws.com/pipeline-s3-bluescapepublicassetsbucket-9ddqpmv4d2h",
    "https://s3.us-west-2.amazonaws.com/pipeline-s3-bluescapepublicassetsbucket-72c15083h4lk",
    "https://s3.us-west-2.amazonaws.com/pipeline-s3-bluescapepublicassetsbucket-1dh5dttbbkhze",
]:
    test("s3", "GET", bucket)

print("\n" + "=" * 80)
print("=== JAM API ===")
print("=" * 80)

jam = "https://api.beta.us-west-2.non-prod.jam.training.aws.dev"
for path in ["/events", "/campaigns", "/challenges", "/admin/terms/status", "/admin/users",
             "/admin/events", "/admin/challenges", "/admin/gdpr/dsar", "/settings", "/apikeys"]:
    test("jam", "GET", f"{jam}{path}")

print("\n" + "=" * 80)
print("=== OPENVAULT / SIT MARKETING ===")
print("=" * 80)

for stage in ["alpha", "beta", "gamma", "prod"]:
    test(f"openvault-{stage}", "GET", f"https://api.us-east-1.{stage}.openvault.marketing.aws.dev/esmpg")
    test(f"openvault-{stage}", "POST", f"https://api.us-east-1.{stage}.openvault.marketing.aws.dev/esmpg",
         body='{}')

print("\n" + "=" * 80)
print("=== SIGNAGE CONSOLE ===")
print("=" * 80)

sig = "https://console.signage.amazon.com"
for path in ["/api/account/api/v1/userInfos", "/api/account/api/v1/dmsUsers",
             "/api/account/api/v1/dmsUsers/admin", "/api/device/dms/api/v1/dmsDevices",
             "/api/device/cms/api/v2/cmsVendorList"]:
    test("signage", "GET", f"{sig}{path}")

print("\n" + "=" * 80)
print("=== BEACON DEVICE MANAGEMENT ===")
print("=" * 80)

test("beacon-login-prod", "GET", "https://api.us-east-1.devicemanagement.amazon/v1/authn/loginUrl",
     headers={"x-amzRedirectUrl": "https://beacon.devices.amazon.dev", "x-amzClientId": "fi2e1l22rhp0630e3jmqi52fq"})
test("beacon-login-beta", "GET", "https://api.beta.us-east-1.lime.devices.amazon.dev/v1/authn/loginUrl",
     headers={"x-amzRedirectUrl": "https://beta.beacon.devices.amazon.dev", "x-amzClientId": "4o7ilpv96kd5usbftkqkmcfq4o"})

for base in ["https://svc.beacon.devices.amazon.dev/api", "https://svc.beta.beacon.devices.amazon.dev/api"]:
    for path in ["/v1/beacon/task-plan", "/v1/beacon/task-template", "/v1/proxy/milestones/schedule"]:
        test("beacon", "GET", f"{base}{path}")

print("\n" + "=" * 80)
print("=== STREAM PROCESSING CONTROL PLANES ===")
print("=" * 80)

for region in ["iad", "nrt"]:
    test(f"stream-{region}", "GET", f"https://api.control-plane.{region}.stream-processing.aft.a2z.com")

print("\n" + "=" * 80)
print("=== BUILDER.AWS.COM ===")
print("=" * 80)

test("builder-config", "GET", "https://builder.aws.com/__runtime-env.js")
test("builder-api", "GET", "https://api.builder.aws.com")

print("\n" + "=" * 80)
print("=== THUNDER / REKOGNITION (34 endpoints - sample) ===")
print("=" * 80)

thunder = [
    "https://eie58kul2e.execute-api.us-west-2.amazonaws.com/test",
    "https://3idm9xgta4.execute-api.us-west-2.amazonaws.com/prod/",
    "https://iki2wh42p7.execute-api.us-west-2.amazonaws.com/prod/",
    "https://j610i7sea1.execute-api.us-west-2.amazonaws.com/prod/",
    "https://v6yv5j34u4.execute-api.us-west-2.amazonaws.com/prod",
    "https://lzos0nnz74.execute-api.us-west-2.amazonaws.com/prod",
    "https://htp4r2298i.execute-api.us-west-2.amazonaws.com/prod",
]
for ep in thunder:
    test("thunder", "GET", ep, "sigv4", "us-west-2")

print("\n" + "=" * 80)
print("DONE. Look for [200/201/204] responses marked with <<<")
print("=" * 80)
