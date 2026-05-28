# Offen hc_scale

- Fehlerbehebung siehe apps_v2/hc_scale/check_result.txt

- routes: api/appstatus geht nicht bei nginx config
  -  api/appstatus: {"detail":"Not Found"}
  -  api/status: {"detail":"Not Found"}

- index.html hat noch css+javascript

- config.py
    # Body Scale Types (deutsch)
    body_scale_types: tuple = (
        "Fettleibig", "Übergewichtig", "Dick", "Bewegungsmangel",
        "Ausgeglichen", "Ausgeglichen Muskulös", "Dünn",
        "Ausgeglichen Dünn", "Dünn Muskulös",
    )
    diff_text: tuple = ("Abgenommen", "Keine Veränderung", "Zugenommen")

    sollten eigentlich in lang.de

- ha_discovery.py viele hard-cored einträge
  - ha_discovery.yaml