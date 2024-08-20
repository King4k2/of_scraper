from seleniumwire import webdriver
import time
import openpyxl
import json


def onlyfans_login():
    wb = openpyxl.load_workbook(filename="OnlyFansConfig.xlsx")
    sh = wb["Sheet1"]  # A - account name ; B - user-agent ; C - sec-ch-ua ; D - cookie
    acc_name = input("input OnlyFans Account name: ")
    a = 0
    for i in range(1, sh.max_row+1):
        if sh[f"A{i}"].value == acc_name:
            a = i
            break
    if a == 0:
        if sh.max_row == 1:
            a = sh.max_row
        else:
            a = sh.max_row+1
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    driver.get("https://onlyfans.com/")
    i = input("Input something: ")
    cookies_ = driver.get_cookies()
    with open(f'{acc_name}_OFS_cookies.json', 'w') as file:
        json.dump(cookies_, file)
    driver.close()
    res = req_interceptor(driver)
    if type(res) is str:
        print(res)
    else:
        sh[f"A{a}"] = acc_name
        sh[f"B{a}"] = res[0]
        sh[f"C{a}"] = res[1]
        sh[f"D{a}"] = res[2]
        sh[f"E{a}"] = res[3]
        wb.save(filename="OnlyFansConfig.xlsx")
        wb.close()

        driver.quit()


def req_interceptor(driver):
    for request in driver.requests:
        if request.url != "https://onlyfans.com/api2/v2/users/me":
            continue
        print(request)
        if request.headers is not None:
            print(request.headers)
            print(request.headers.get("sec-ch-ua"))
            print(request.headers.get("user-agent"))
            print(request.headers.get("cookie"))

            print("\n-----------------\n")
            return [request.headers.get("user-agent"), request.headers.get("accept-language"),
                    request.headers.get("sec-ch-ua"), request.headers.get("cookie")]
    return "Something went wrong. Try again"


if __name__ == "__main__":
    onlyfans_login()