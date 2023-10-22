from langchain.tools import BaseTool
from xiaogpt.langchain.examples.email.mail_box import Mailbox


class MailSummaryTool(BaseTool):
    name = "MailSumary"
    description = "当被问到总结邮件相关时，会触发这个工具，进行今日邮件总结和发送。当调用工具完毕，只需要回复总结成功或失败即可，立即结束本次回答"

    def get_mail_summary(self) -> str:
        """
        总结邮件：对邮箱内收到的邮件进行总结，并发送到指定邮箱
        """
        mailbox = Mailbox()
        all_email_content = mailbox.get_all_work_summary()
        prompt = """
        要求你作为一名总编辑。根据输入的多封邮件，对每封做简明扼要的摘要。要求如下：
        1、对每封邮件摘要总结，摘要总结字数在25字以内
        2、排版按照 发送人：xx 内容：xx （换一行）
        3、注意换行，要求全文美观简洁
        4、展示邮件内提到项目名，不用额外扩展讲项目内容和进度
        """
        gpt_content = mailbox.get_summary_by_ai(all_email_content, prompt)
        is_success = mailbox.send_mail(gpt_content)
        if is_success:
            return "总结邮件成功"
        else:
            return "总结邮件失败，请检查邮箱配置"

    def _run(self, query: str) -> str:
        return self.get_mail_summary()

    async def _arun(self, query: str) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("MailSummaryTool does not support async")
