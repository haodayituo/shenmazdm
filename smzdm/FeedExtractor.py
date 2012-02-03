#! /usr/bin/python
# -*- coding: utf8 -*-

from lxml import etree
from lxml.cssselect import CSSSelector
from datetime import date, time
import lxml.html as html
import urllib2
import re
import string


###################################################################
class SMZDM_ProductInfo(object):

  def __init__ (self):
    self.post_id      = None
    self.title        = None
    self.url        = None    
    self.publish_datetime = None 
    self.number_of_comments = None
    self.content_html   = None
    self.category     = []
    self.tags       = []
  
class SMZDM_FeedExtractor(object):
  url_string  = 'http://www.smzdm.com'
  text_encoding = 'utf8'

  def __page_at_index(self, index=1):
    url = SMZDM_FeedExtractor.url_string + '/page/%d' % index
    page_content = urllib2.urlopen(url).read()
    return html.document_fromstring(page_content)


  def __productinfo_from_page(self, page):
    result = []

    for post_element in CSSSelector('div.post[id^="post-"]')(page):
      product_info = SMZDM_ProductInfo()

      # post_id
      m = re.match('post-(\d*)', ''.join(post_element.get('id').split()))
      if m:
        product_info.post_id = m.group(1)

      # title
      title_a = post_element.xpath("h2/a")[0]
      product_info.title  = title_a.text
      
      # link
      product_info.url    = title_a.get("href")

      info_div =  post_element.xpath("div[@class='info']")[0]
      
      # publish_datetime
      tmpstr = info_div.xpath("span[@class='date']")[0].text
      # Remove blank charactors
      m = re.match(u'(\d*)年(\d*)月(\d*)日', ''.join(tmpstr.split()))
      if m and len(m.groups()) == 3:
        tl = m.groups()
        product_info.publish_datetime = date(int(tl[0]), int(tl[1]), int(tl[2]))

      # number_of_comments
      tmpstr = info_div.xpath("span[@class='comments']/a")[0].text
      m = re.match("(\d*)", ''.join(tmpstr.split()))
      if m  and len(m.group(1)) > 0:
        product_info.number_of_comments = int(m.group(1))
      else:
        product_info.number_of_comments = 0
      
      # content_html
      content_div = post_element.xpath("div[@class='content']")[0]
      product_info.content_html = etree.tostring( content_div, 
                            encoding=SMZDM_FeedExtractor.text_encoding, 
                            method='html',
                            pretty_print=True )
      
      # category and tags
      under_div = post_element.xpath("div[@class='under']")[0]
      for a in under_div.xpath("//a[@rel='category tag']"):
        product_info.category.append(a.text)
      for a in  under_div.xpath("//a[@rel='tag']"):
        product_info.tags.append(a.text)

      result.append(product_info)  
      
    return result


  def get_product_list(self, post_id = '', maxCount=15):
    result = []

    page_index = 1
    while(True) :
      tmp_list = self.__productinfo_from_page(self.__page_at_index(page_index))
      
      should_break = False

      for info in tmp_list:
        
        if len(result) >= maxCount or \
            ( len(post_id) > 0 and int(post_id) >= int(info.post_id) ):
          should_break = True
          break;
      
        result.append(info)
          
      if should_break : 
        break;

      # Try to get next page
      page_index += 1

    return result
      

    
########################################################################################################

import threading
from threading import Timer, Thread
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
import time
import smtplib

def send_email_thread_method(receiver='', content=''):
  sender = 'xubenyang@gmail.com'

  message = MIMEMultipart()
  message.attach(MIMEText(content))
  message['Subject']  = 'New post from SMZDM'
  message['From']     = sender
  message['To']   = receiver

  try:
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(sender, 'bageyalu1?')
    server.sendmail(sender, receiver, message.as_string())
    server.close()  
    print "* Successfully sent email"
  except SMTPException:
    print "* Error: unable to send email"


def send_email(receiver='', content=''):
  threading.Thread(target = send_email_thread_method, args=(receiver, content)).start()
  

def crawl_after_post_id(post_id=''):
  lastest_post_id = post_id

  extractor = SMZDM_FeedExtractor()
  info_list = extractor.get_product_list(post_id, 15)

  if len(info_list) > 0:
    lastest_post_id = info_list[0].post_id

  return (info_list, lastest_post_id)


def continue_crawl_after_post_id(post_id=''):

  value = crawl_after_post_id(post_id)

  new_products = value[0]
  print 'NEW: ' + str(len(new_products))
  
  # Send Email
  if len(new_products) > 0:
    content = []

    for product in new_products: 
      content.append("%s\n%s\n%s\n" % (product.title, product.url, str(product.publish_datetime)))

    content_str = str(len(new_products)) + '\n-------------------------------------------\n'\
        + string.join(content, '-------------------------------------------\n')

    send_email('benyang.xu@qq.com', 'NEW PRODUCTS: ' + content_str.encode('utf8'))


  Timer(5, continue_crawl_after_post_id, [value[1]]).start()


########################################################################################################


# run test cases if it's main

if __name__ == '__main__':

  continue_crawl_after_post_id()
  
  while True:
    time.sleep(1)




