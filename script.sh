export BASE_URL='https://qbank-api.collegeboard.org/msreportingquestionbank-prod/questionbank/digital/'
export HEADERS="-H 'accept:application/json' \
  -H 'accept-language:en-US,en;q=0.6' \
  -H 'content-type:application/json' \
  -H 'origin:https://satsuitequestionbank.collegeboard.org' \
  -H 'priority:u=1,i' \
  -H 'referer:https://satsuitequestionbank.collegeboard.org/' \
  -H 'sec-ch-ua:'Brave';v='129', 'Not=A?Brand';v='8', 'Chromium';v='129'' \
  -H 'sec-ch-ua-mobile:?0' \
  -H 'sec-ch-ua-platform:'Linux'' \
  -H 'sec-fetch-dest:empty' \
  -H 'sec-fetch-mode:cors' \
  -H 'sec-fetch-site:same-site' \
  -H 'sec-gpc:1' \
  -H 'user-agent:Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'"

echo $(curl 'https://qbank-api.collegeboard.org/msreportingquestionbank-prod/questionbank/digital/get-questions' \
  -X 'OPTIONS' \
  -H 'accept: */*' \
  -H 'accept-language: en-US,en;q=0.9' \
  -H 'access-control-request-headers: content-type' \
  -H 'access-control-request-method: POST' \
  -H 'origin: https://satsuitequestionbank.collegeboard.org' \
  -H 'priority: u=1, i' \
  -H 'referer: https://satsuitequestionbank.collegeboard.org/' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-site' \
  -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36')

curl $HEADERS --data-raw '{'asmtEventId':100,'test':2,'domain':'H,P,Q,S'}' $BASE_URL > data.txt