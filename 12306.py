from selenium import webdriver
from selenium.webdriver.common.by import By
from config import Config
from selenium.webdriver.common.keys import Keys
import time


def get_ticket(conf, driver, url):
    # 过网站检测，没加这句的话，账号密码登录时滑动验证码过不了，但二维码登录不受影响
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
                           {"source": """Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"""})
    driver.maximize_window()
    driver.get(url)
    # 最多等待5秒使页面加载进来，隐式等待
    driver.implicitly_wait(5)

    # 获取并点击右上角登录按钮
    login = driver.find_element(by=By.ID, value='J-btn-login')
    login.click()
    driver.implicitly_wait(10)

    # 账号密码登录
    username_tag = driver.find_element(by=By.ID, value='J-userName')
    username_tag.send_keys(conf.username)
    password_tag = driver.find_element(by=By.ID, value='J-password')
    password_tag.send_keys(conf.password)
    login_now = driver.find_element(by=By.ID, value='J-login')
    login_now.click()
    time.sleep(2)

    id_last = driver.find_element(By.ID, 'id_card')
    id_last.send_keys(conf.id_last)
    # 过滑动验证码，但是现在要求输入身份证尾号和要验证码，这里自己看着输
    # picture_start = driver.find_element(by=By.ID, value='nc_1_n1z')
    # 移动到相应的位置，并左键鼠标按住往右边拖
    # ActionChains(driver).move_to_element(picture_start)
    # .click_and_hold(picture_start).move_by_offset(300, 0).release().perform()

    '''
    # 扫码登录
    scan_QR = driver.find_element(by=By.XPATH, value='//*[@id="toolbar_Div"]/div[2]/div[2]/ul/li[2]/a')
    scan_QR.click()
    driver.implicitly_wait(10)
    '''

    # 因为脚本控制的默认第一次登录，有提示框弹出就点提示框
    try:
        driver.find_element(by=By.XPATH, value='//div[@class="dzp-confirm"]/div[2]/div[3]/a').click()
        driver.implicitly_wait(5)
    except:
        pass
    # 点击车票预订跳转到预订车票页面
    driver.find_element(by=By.XPATH, value='//*[@id="link_for_ticket"]').click()
    driver.implicitly_wait(10)

    # 输入出发地和目的地信息
    # 出发地
    driver.find_element(by=By.XPATH, value='//*[@id="fromStationText"]').click()
    driver.find_element(by=By.XPATH, value='//*[@id="fromStationText"]').clear()
    driver.find_element(by=By.XPATH, value='//*[@id="fromStationText"]').send_keys(conf.fromstation)
    time.sleep(1)
    driver.find_element(by=By.XPATH, value='//*[@id="fromStationText"]').send_keys(Keys.ENTER)

    # 目的地
    destination_tag = driver.find_element(by=By.XPATH, value='//*[@id="toStationText"]')
    destination_tag.click()
    destination_tag.clear()
    destination_tag.send_keys(conf.destination)
    time.sleep(1)
    destination_tag.send_keys(Keys.ENTER)
    driver.implicitly_wait(5)

    # 出发日期
    date_tag = driver.find_element(by=By.XPATH, value='//*[@id="train_date"]')
    date_tag.click()
    date_tag.clear()
    date_tag.send_keys(conf.date)
    time.sleep(1)
    query_tag = driver.find_element(by=By.XPATH, value='//*[@id="query_ticket"]')

    start = time.time()

    while True:
        # 隐形等待5秒
        driver.implicitly_wait(5)
        try:
            # 点击查询
            driver.execute_script("$(arguments[0]).click()", query_tag)
            # 获取所有车票
            tickets = driver.find_elements(by=By.XPATH, value='//*[@id="queryLeftTable"]/tr')
            # 每张车票有两个tr，但是第二个tr没什么用
            tickets = [tickets[i] for i in range(len(tickets) - 1) if i % 2 == 0]
            a = tickets[0].find_element(By.XPATH, '//td[13]').text
        except:
            query_tag = driver.find_element(by=By.XPATH, value='//*[@id="query_ticket"]')
            print('页面加载中......')
            continue
        # 如果开售的话，a里面的内容会变成预订
        if a != '预订':
            print(f"{a}，现在是{time.strftime('%H:%M:%S', time.localtime())}，还未开始售票.")
            # 三分钟以上没有进行购票操作的话，12306会自动登出
            if time.time() - start >= 120:
                driver.refresh()
                start = time.time()
            # 防止点击太频繁导致查询超时，会使页面停止一段时间
            time.sleep(0.5)
            continue
        for ticket in tickets:
            # 这里检查一下票的车次是否正确，正确的话会直接点预订，因为时前几秒抢票，所以不考虑判断是否已经开始候补
            # if ticket.find_element(by=By.CLASS_NAME,value='cdz').text== conf.fromstation:
            # value = '//td[8]'表示硬卧，td[10]表示硬座
            if ticket.find_element(by=By.CLASS_NAME, value='number').text == conf.trainnumber:
                # 打印票的轮次
                print(ticket.find_element(by=By.CLASS_NAME, value='number').text)
                # 打印出发地和目的地
                print(ticket.find_element(by=By.CLASS_NAME, value='cdz').text)
                # 找到这张票对应的预订按钮
                try:
                    yu_ding = ticket.find_element(by=By.CLASS_NAME, value='btn72')
                except:
                    yu_ding = None
                if yu_ding is not None:
                    yu_ding.click()
                    print(yu_ding.text)
                    # 这里之后就不能继续使用ticket.find_element()了，因为页面进行了跳转，
                    # 会出现stale element reference: element is not attached to the page document的错误
                    # 我们可以使用driver.find_element()
                    # 选择默认的第一个乘车人，如果是学生，则需要确认购买学生票
                    passenger = driver.find_element(by=By.XPATH, value='//*[@id="normalPassenger_0"]')
                    passenger.click()
                    # 对于学生票，需要点击确认购买学生票，如果不是学生，把这行注释了就行
                    driver.find_element(by=By.XPATH, value='//*[@id="dialog_xsertcj_ok"]').click()
                    print('确认')
                    # 第二个乘车人
                    # driver.find_element(by=By.XPATH, value='//*[@id="normalPassenger_1"]').click()
                    # 如果第二个乘车人也是学生，则需要点击确认第二个人也购买学生票
                    # driver.find_element(by=By.XPATH, value='//*[@id="dialog_xsertcj_ok"]').click()
                    # 提交订单
                    driver.find_element(by=By.XPATH, value='//*[@id="submitOrder_id"]').click()
                    print('提交订单中......')
                    # 选座  F座
                    # 学生票不支持选座
                    # time.sleep(1)
                    # move = driver.find_element(By.ID, value='1F')
                    # ActionChains(driver).move_to_element(move).perform()
                    # time.sleep(1)
                    # 这里直接使用id和xpath定位不到，所以直接加上他的路径,可以不用这么长，但是懒得删
                    try:
                        driver.find_element(by=By.XPATH,
                                            value='//html/body/div[5]/div/div[5]/div[1]/div/div[2]/div[2]/div[3]/div[2]'
                                                  '/div[2]/ul[2]/li[2]/a[@id="1F"]').click()
                    except:
                        pass
                    # 确认提交订单，然后这里和上面是一样的
                    driver.find_element(by=By.ID, value='qr_submit_id').click()
                    print(f"{conf.trainnumber}次列车抢票成功，请尽快在10分钟内支付！")
                    time.sleep(600)
                    return
                else:
                    print('抢票失败!本次列车票已售罄!')
                    return


if __name__ == '__main__':
    # 有关车票的配置信息保存在该类里
    # 请事先在config.py里填好相关信息
    conf = Config()

    url = 'https://www.12306.cn/index/'

    # 这里需要根据你电脑上所拥有的浏览器类型来进行选择
    driver = webdriver.Chrome()
    get_ticket(conf, driver, url)
    time.sleep(10)
    driver.quit()
