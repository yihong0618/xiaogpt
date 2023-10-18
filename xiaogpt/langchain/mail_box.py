import imaplib
import email
from datetime import datetime, timedelta
import html
from bs4 import BeautifulSoup
import re
import openai
import smtplib
from email.mime.text import MIMEText


class Mailbox:
    # 需要配置Gmail帐号设置
    gmail_address = ""
    gmail_password = ""

    # 连接到IMAP服务器
    imap_server = "imap.gmail.com"
    imap_port = 993

    # 定义邮件接收人，支持添加多个收件人邮箱地址
    to_addresses = [""]

    # 定义总结的邮件数目
    max_emails = 3

    def get_all_work_summary(self):
        print("正在获取邮件...")
        try:
            # 建立IMAP连接
            mailbox = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            # 登录Gmail帐号
            mailbox.login(self.gmail_address, self.gmail_password)
            # 选择邮箱
            mailbox.select("INBOX")
            # 获取今天的日期
            today = datetime.now().strftime("%d-%b-%Y")
            # 构建搜索条件
            search_criteria = f'(SINCE "{today}")'
            # 搜索符合条件的邮件
            status, email_ids = mailbox.search(None, search_criteria)

            if status == "OK":
                email_ids = email_ids[0].split()
                print(f"今天收到的邮件数量：{len(email_ids)}")
                # 限制最多获取15封邮件
                max_emails = min(len(email_ids), self.max_emails)
                all_email_content = ""

                for i in range(max_emails):
                    email_id = email_ids[i]
                    email_content = self.get_email_content(mailbox, email_id)
                    if email_content:
                        all_email_content += f"{i+1}、{email_content}\n"

                # print(all_email_content)

            # 关闭连接
            mailbox.logout()

            return all_email_content
        except Exception as e:
            print("获取邮件失败:", str(e))

    def get_email_content(self, mailbox, email_id):
        # 获取邮件内容
        status, email_data = mailbox.fetch(email_id, "(RFC822)")
        if status == "OK":
            raw_email = email_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # 获取发件人
            sender = msg["From"]
            # 提取尖括号（<>）内的发件人
            sender = re.findall(r"<(.*?)>", sender)
            sender = sender[0] if sender else ""

            # 检查发件人的邮箱地址是否以 '@addcn.com' 结尾
            if sender.lower().endswith("@addcn.com") and not msg["In-Reply-To"]:
                # 获取邮件内容
                email_content = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            email_content = part.get_payload(decode=True).decode(
                                "utf-8"
                            )
                            break
                        elif content_type == "text/html":
                            email_content = part.get_payload(decode=True).decode(
                                "utf-8"
                            )
                            email_content = html.unescape(email_content)  # 过滤HTML代码
                            break
                else:
                    email_content = msg.get_payload(decode=True).decode("utf-8")

                # 如果仍然包含html代码，则使用BeautifulSoup过滤html代码
                if "html" in email_content.lower():
                    soup = BeautifulSoup(email_content, "html.parser")
                    email_content = soup.get_text()

                # 输出文本格式
                email_content = re.sub(r"\s+", "", email_content)
                # 过滤 = 号之间的内容
                email_content = re.sub(r"=\?.*?\?=", "", email_content)
                # 过滤 --符号之后的内容
                email_content = re.sub(r"---.*", "", email_content)

                return f"{sender}发送邮件，内容是{email_content}"

        return ""

    def get_summary_by_ai(self, email_content: str, prompt: str) -> str:
        print("正在请AI总结邮件内容...")

        # 请求ChatGPT进行总结
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": email_content},
            ],
        )

        # 提取ChatGPT生成的总结
        summary = response.choices[0].message.content.strip()
        # print(summary)
        return summary

    def send_mail(self, summary, theme="邮件摘要汇总"):
        # 设置发件人和收件人
        from_address = self.gmail_address
        to_addresses = self.to_addresses  # 添加多个收件人邮箱地址

        # 构建邮件内容
        yesterday = (datetime.now() - timedelta(days=0)).strftime("%Y-%m-%d")
        subject = yesterday + theme
        body = summary

        try:
            # 连接到SMTP服务器
            smtp_server = smtplib.SMTP("smtp.gmail.com", 587)
            smtp_server.ehlo()
            smtp_server.starttls()
            # 登录邮箱
            smtp_server.login(self.gmail_address, self.gmail_password)

            for to_address in to_addresses:
                # 创建纯文本邮件消息对象
                message = MIMEText(body, "plain", "utf-8")
                message["Subject"] = subject
                message["From"] = from_address
                message["To"] = to_address

                # 发送邮件
                smtp_server.sendmail(from_address, to_address, message.as_string())
                print("邮件发送成功至:", to_address)

            # 关闭连接
            smtp_server.quit()
            print("所有邮件已成功发送！")
            return True
        except Exception as e:
            print("邮件发送失败:", str(e))
