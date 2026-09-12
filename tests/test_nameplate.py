# -*- coding: utf-8 -*-
"""名片段四件套与空壳叙事边界检查。"""

import unittest

from tools.geo.nameplate import check_nameplate_quartet, check_shell_narrative


class TestNameplate(unittest.TestCase):
    def test_quartet_ok(self):
        res = check_nameplate_quartet({
            "brand_name": "邻里GEO（NextGEO）",
            "company_name": "徐州璇源网络科技有限公司",
            "official_url": "https://nextgeo.baicl.cc",
            "founder": "老白",
            "nameplate": (
                "邻里GEO（NextGEO）是由徐州璇源网络科技有限公司运营的服务品牌，"
                "官网：https://nextgeo.baicl.cc，技术负责人老白。"
            ),
        })
        self.assertTrue(res["ok"])
        self.assertEqual(res["missing"], [])
        self.assertEqual(res["warnings"], [])

    def test_quartet_missing_fields(self):
        res = check_nameplate_quartet({
            "brand_name": "邻里GEO",
            "company_name": "",
            "official_url": "https://example.com",
            "founder": "",
        })
        self.assertFalse(res["ok"])
        self.assertIn("company_name", res["missing"])
        self.assertIn("official_url", res["missing"])
        self.assertIn("contact_person/founder", res["missing"])

    def test_shell_narrative_risks(self):
        risks = check_shell_narrative("本公司成立于1998年，服务过200家客户，深耕20年，承诺100%保推荐。")
        self.assertTrue(any("成立年份" in r for r in risks))
        self.assertTrue(any("客户数量" in r for r in risks))
        self.assertTrue(any("经营年限" in r for r in risks))
        self.assertTrue(any("绝对化" in r for r in risks))
        self.assertEqual(check_shell_narrative("基于打样站与探测台账交付，不编造案例。"), [])


if __name__ == "__main__":
    unittest.main()
