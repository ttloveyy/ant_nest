from yarl import URL
from ant_nest.ant import Ant
from ant_nest.pipelines import ItemFieldReplacePipeline
from ant_nest.things import ItemExtractor


class GithubAnt(Ant):
    """Crawl trending repositories from github"""

    item_pipelines = [
        ItemFieldReplacePipeline(
            ("meta_content", "star", "fork"), excess_chars=("\r", "\n", "\t", "  ")
        )
    ]
    concurrent_limit = 1  # save the website`s and your bandwidth!

    def __init__(self):
        super().__init__()
        self.item_extractor = ItemExtractor(dict)
        self.item_extractor.add_pattern("xpath", "title", "//h1/strong/a/text()")
        self.item_extractor.add_pattern(
            "xpath", "author", "//h1/span/a/text()", default="Not found"
        )
        self.item_extractor.add_pattern(
            "xpath",
            "meta_content",
            '//div[@class="repository-content "]/div[2]//text()',
            extract_type=ItemExtractor.EXTRACT_WITH_JOIN_ALL,
            default="Not found!",
        )
        self.item_extractor.add_pattern(
            "xpath", "star", '//a[@class="social-count js-social-count"]/text()'
        )
        self.item_extractor.add_pattern(
            "xpath", "fork", '//a[@class="social-count"]/text()'
        )

    async def crawl_repo(self, url):
        """Crawl information from one repo"""
        response = await self.request(url)
        # extract item from response
        item = self.item_extractor.extract(response)
        item["origin_url"] = response.url

        await self.collect(item)  # let item go through pipelines(be cleaned)
        self.logger.info("*" * 70 + "I got one hot repo!\n" + str(item))

    async def run(self):
        """App entrance, our play ground"""
        response = await self.request("https://github.com/explore")
        for url in response.html_element.xpath(
            "/html/body/div[4]/main/div[2]/div/div[2]/div[1]/article/div/div[1]/h1/a[2]/"
            "@href"
        ):
            # crawl many repos with our coroutines pool
            self.schedule_task(self.crawl_repo(response.url.join(URL(url))))
        self.logger.info("Waiting...")
