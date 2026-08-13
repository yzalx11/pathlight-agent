from app.services.jobs import infer_job_metadata


def test_infers_boss_job_metadata_from_ocr_text():
    metadata = infer_job_metadata(
        """AI Agent开发工程师
10-15K
杭州 1-3年 本科
职位描述
岗位职责：参与 AI Agent 应用开发。"""
    )

    assert metadata["title"] == "AI Agent开发工程师"
    assert metadata["salary"] == "10-15K"
    assert metadata["city"] == "杭州"
    assert metadata["experience"] == "1-3年"
    assert metadata["education"] == "本科"
