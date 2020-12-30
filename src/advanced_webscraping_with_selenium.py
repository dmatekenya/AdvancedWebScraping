from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def extract_job_posts(driver, results_table):
    """
    Given results on a single page, extract the job details
    :param driver:
    :type driver:
    :param results_table:
    :type results_table:
    :return:
    :rtype:
    """
    data = []

    for i in results_table:
        try:
            if not i.text:
                continue
            i.click()
            windows = driver.window_handles
            if len(windows) == 1:
                continue
            driver.switch_to.window(windows[-1])
            try:
                pos_title = driver.find_element_by_xpath('//*[contains(@id,"jobPostingTitle")]').text
                grade = pos_title.split(",")[-1]
            except:
                grade = 'Not specified'

            try:
                job_code = driver.find_element_by_xpath('//*[contains(@id,"jobCodeTitle")]').text
            except:
                job_code = i.text

            duty_station = driver.find_element_by_xpath('//*[contains(@id,"jobDutystation")]').text
            period = driver.find_element_by_xpath('//*[contains(@id,"jobPeriod")]').text
            url = driver.current_url
            pos_html = {'Title': job_code, 'Grade': grade, 'DutyStation': duty_station,
                        'PostingPeriod': period, 'url': url}
            data.append(pos_html)
            driver.close()
            driver.switch_to.window(windows[0])
        except Exception as e:
            print(e)
            driver.switch_to.window(windows[0])
            continue
    return data


def get_number_of_pages(guessed_num_pages=40):
    """
    Determine number of pages on the site.
    :return: Number of pages
    :rtype:
    """
    with webdriver.Firefox() as driver:
        driver.get("https://careers.un.org/lbw/home.aspx?lang=en-US")
        driver.find_element(By.ID,
                            "ctl00_ContentPlaceHolder1_UNCareersLoader1_ctl00_SearchControl1_btnSearch").send_keys(
            Keys.RETURN)

        driver.implicitly_wait(10)
        next_page = driver.find_element_by_link_text(">>")
        next_page.click()
        tr_rows = driver.find_elements_by_tag_name("tr")
        try:
            for tr in tr_rows:
                if "<<" in tr.text:
                    txt = tr.text.split(" ")[-1]
                    driver.close()
                    return int(txt)
        except:
            # if above fails, just return a large number
            driver.close()
            return guessed_num_pages


def get_search_results_from_page(driver, page):
    """
    Helper function to extract search results matching job posts
    :return:
    :rtype:
    """
    if page > 1:
        driver.implicitly_wait(10)
        next_page = None
        if page == 11:
            next_page = driver.find_element_by_link_text("...")
        elif page == 21:
            elements = driver.find_elements_by_link_text("...")
            for i in elements:
                if str(page) in i.get_attribute("href"):
                    next_page = i
                    break
        else:
            next_page = driver.find_element_by_link_text(str(page))
        next_page.click()
        results_table = driver.find_elements_by_xpath('//*[contains(@id,"gvSearchGrid")]')
    else:
        driver.implicitly_wait(10)
        results_table = driver.find_elements_by_xpath('//*[contains(@id,"gvSearchGrid")]')

    return results_table


def search_with_selenium(url="https://careers.un.org/lbw/home.aspx?lang=en-US"):
    """
    Takes the base url and searches for all professional jobs
    :return: A list of dict items which have
    :rtype:
    """
    num_pages = get_number_of_pages()
    print("Found {} pages".format(num_pages))
    with webdriver.Firefox() as driver:
        driver.get(url)
        driver.find_element(By.ID,
                            "ctl00_ContentPlaceHolder1_UNCareersLoader1_ctl00_SearchControl1_btnSearch").send_keys(
            Keys.RETURN)

        data = []
        for page in range(1, num_pages + 1):
            try:
                results_table = get_search_results_from_page(driver, page)
                data += extract_job_posts(driver, results_table)
            except:
                pass
    return data


def find_relevant_jobs(job_title):
    key_words = ["data", "statistics", "statistician", "research", "monitoring", "census"]
    for k in key_words:
        if k in job_title.lower():
            return 1
    return 0


def process_job_items():
    res = search_with_selenium()
    df = pd.DataFrame(res)
    df['relevant'] = df['Title'].apply(find_relevant_jobs)
    df = df[df['relevant'] == 1]
    df.drop(labels=['relevant'], axis=1, inplace=True)
    out_csv = Path.cwd.parents[1].joinpath("scraped_files", 'UNCareers.csv')
    df.to_csv(out_csv, index=False)