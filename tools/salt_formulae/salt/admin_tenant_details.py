found_id = False
admin_id = None
with open("/srv/salt/admin_tenant_details.txt", "r") as fopen:
    for data in fopen:
        if data.strip() == "id:":
            found_id = True
            continue
        if found_id:
            admin_id = data.strip()
            break
if found_id:
    print(admin_id)
