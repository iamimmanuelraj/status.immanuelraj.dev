import yaml, os, sys, time
from requests import head
from concurrent.futures import ThreadPoolExecutor, as_completed

issues = []
restored = []
nstatus = {}


def is_up(url):
    retries = 0
    max_retries = 3  # Reduced from 10 to 3
    timeout = 5  # 5 second timeout per request
    while retries < max_retries:
        try:
            response = head(url, timeout=timeout, allow_redirects=True)
            status_code = response.status_code
            print("Status code: " + str(status_code))
            if status_code == 200 or status_code == 302 or status_code == 301 or status_code == 307 or status_code == 401:
                return True
        except Exception as e:
            print(e)
        retries += 1
        if retries < max_retries:
            time.sleep(1)  # Reduced from 5 to 1 second
    return False


def check_site(gname, site, ostatus):
    """Check a single site and return its status"""
    sname = site["name"]
    url = site["url"]
    print("Checking: " + sname)
    
    result = {
        'gname': gname,
        'sname': sname,
        'url': url,
        'status': None,
        'is_restored': False,
        'issue': None
    }
    
    if is_up(url):
        is_restored = (
            gname in ostatus
            and sname in ostatus[gname]["sites"]
            and ostatus[gname]["sites"][sname] != "operational"
        )
        result['status'] = "operational"
        result['is_restored'] = is_restored
    else:
        ostatus_gname = ostatus.get(gname, {})
        ostatus_sites = ostatus_gname.get("sites", {})
        
        if sname in ostatus_sites:
            if ostatus_sites[sname] == "operational":
                result['status'] = "partial"
                result['issue'] = {"name": sname, "url": url}
            else:
                result['status'] = "major"
        else:
            result['status'] = "partial"
            result['issue'] = {"name": sname, "url": url}
    
    return result


try:
    ostatus = yaml.load(open("_data/status.yml"), Loader=yaml.FullLoader)
except:
    open("_data/status.yml", "a").close()
    ostatus = yaml.load(open("_data/status.yml"), Loader=yaml.FullLoader)

try:
    tracker = yaml.load(open("_data/tracker.yml"), Loader=yaml.FullLoader)
except:
    print("_tracker.yml not found. Cannot check for status.")

# Initialize nstatus for all groups first
for group in tracker:
    gname = group["group"]
    print("Running status check for group {}".format(gname))
    nstatus[gname] = {}
    nstatus[gname]["sites"] = {}

# Prepare all sites to check
sites_to_check = []
for group in tracker:
    gname = group["group"]
    for site in group["sites"]:
        sites_to_check.append((gname, site))

# Check all sites in parallel using ThreadPoolExecutor
max_workers = 10  # Check up to 10 sites concurrently
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # Submit all tasks
    future_to_site = {
        executor.submit(check_site, gname, site, ostatus): (gname, site)
        for gname, site in sites_to_check
    }
    
    # Process results as they complete
    for future in as_completed(future_to_site):
        try:
            result = future.result()
            gname = result['gname']
            sname = result['sname']
            
            # Store site status (thread-safe because we pre-initialized all groups)
            nstatus[gname]["sites"][sname] = result['status']
            
            # Track restored sites
            if result['is_restored']:
                restored.append(sname)
            
            # Track issues
            if result['issue']:
                issues.append(result['issue'])
                
        except Exception as e:
            print(f"Error processing site: {e}")

for status in nstatus:
    s = nstatus[status]["sites"].values()
    partial = "partial" if "partial" in s else None
    check = "major" if "major" in s else partial

    if check is None:
        nstatus[status]["group-status"] = "operational"
    else:
        nstatus[status]["group-status"] = check

header = []
for status in nstatus:
    if "Personal" not in status:
        s = nstatus[status]["group-status"]
        header.append(s)

if "major" in header:
    nstatus["statement"] = "We are suffering a major outage"
    nstatus["status-class"] = "critical"
elif "major" not in header and "partial" in header:
    nstatus["statement"] = "We are suffering a partial outage"
    nstatus["status-class"] = "partial"
elif "major" not in header and "partial" not in header and "operational" in header:
    nstatus["statement"] = "All systems are operational"
    nstatus["status-class"] = "no-issues"

f = open("_data/status.yml", "w+")
f.write(yaml.dump(nstatus))
f.close()

f = open("_data/issues.yml", "w+")
f.write(yaml.dump(issues))
f.close()

f = open("_data/restored.yml", "w+")
f.write(yaml.dump(restored))
f.close()
