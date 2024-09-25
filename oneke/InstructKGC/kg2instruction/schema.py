wiki_cate_schema_zh = {
    '人物': [
        '出生地点', [['人物'],['地理地区']],
        '出生日期', [['人物'],['时间']], 
        '国籍', [['人物'],['地理地区']], 
        '职业', [['人物'],['专业']], 
        '作品', [['人物'],['产品']], 
        '成就', [['人物'],['专业']], 
        '籍贯', [['人物'],['地理地区']], 
        '职务', [['人物'],['专业']], 
        '配偶', [['人物'],['人物']], 
        '父母', [['人物'],['人物']], 
        '别名', [['人物'],['人物']], 
        '所属组织', [['人物'],['组织']], 
        '死亡日期', [['人物'],['时间']], 
        '兄弟姊妹', [['人物'],['人物']], 
        '墓地', [['人物'],['地理地区']],
    ], 
    '地理地区': [
        '位于', [['地理地区'],['地理地区']], 
        '别名', [['地理地区'],['地理地区']], 
        '人口', [['地理地区'],['度量']], 
        '行政中心', [['地理地区'],['地理地区']], 
        '面积', [['地理地区'],['度量']], 
        '成就', [['地理地区'],['专业']], 
        '长度', [['地理地区'],['度量']], 
        '宽度', [['地理地区'],['度量']], 
        '海拔', [['地理地区'],['度量']],
    ], 
    '建筑': [
        '位于', [['建筑','地理地区'],['地理地区']], 
        '别名', [['建筑'],['建筑']], 
        '成就', [['建筑'],['专业']], 
        '事件', [['建筑'],['事件']], 
        '创建时间', [['建筑'],['时间']], 
        '宽度', [['建筑'],['度量']], 
        '长度', [['建筑'],['度量']], 
        '创建者', [['建筑'],['人物', '组织']], 
        '高度', [['建筑'],['度量']], 
        '面积', [['建筑'],['度量']], 
        '名称由来', [['建筑'],[]],
    ], 
    '作品': [
        '作者', [['产品'],['人物']], 
        '出版时间', [['产品'],['时间']], 
        '别名', [['产品'],['产品']], 
        '产地', [['产品'],['地理地区']], 
        '改编自', [['产品'],['产品']], 
        '演员', [['产品'],['人物','组织']], 
        '出版商', [['产品'],['组织']], 
        '成就', [['产品'],['专业']], 
        '表演者', [['产品'],['人物','组织']], 
        '导演', [['产品'],['人物','组织']], 
        '制片人', [['产品'],['人物','组织']], 
        '编剧', [['产品'],['人物','组织']], 
        '曲目', [['产品'],['产品']], 
        '作曲者', [['产品'],['人物','组织']], 
        '作词者', [['产品'],['人物','组织']], 
        '制作商', [['产品'],['组织']], 
        '票房', [['产品'],['度量']], 
        '出版平台', [['产品'],['组织']]
    ], 
    '生物': [
        '分布', [['生物'],['地理地区']], 
        '父级分类单元', [['生物'],['地理地区']], 
        '长度', [['生物'],['度量']], 
        '主要食物来源', [['生物'],[]], 
        '别名', [['生物'],['生物']], 
        '学名', [['生物'],['生物']], 
        '重量', [['生物'],['度量']], 
        '宽度', [['生物'],['度量']], 
        '高度', [['生物'],['度量']]
    ], 
    '人造物件': [
        '别名', [['产品'],['产品']], 
        '品牌', [['产品'],['组织']], 
        '生产时间', [['产品'],['时间']], 
        '材料', [['产品'],['产品']], 
        '产地', [['产品'],['地理地区']], 
        '用途', [['产品'],[]], 
        '制造商', [['产品'],['组织']], 
        '发现者或发明者', [['产品'],['人物','组织']]
    ], 
    '自然科学': [
        '别名', [['产品'],['产品']], 
        '性质', [['产品'],[]], 
        '组成', [['产品'],['产品']], 
        '生成物', [['产品'],['产品']], 
        '用途', [['产品'],[]], 
        '产地', [['产品'],['地理地区']], 
        '发现者或发明者', [['产品'],['人物', '组织']]
    ], 
    '组织': [
        '位于', [['组织','地理地区'],['地理地区']], 
        '别名', [['组织'],['组织']], 
        '子组织', [['组织'],['组织']], 
        '成立时间', [['组织'],['组织']], 
        '产品', [['组织'],['组织']], 
        '成就', [['组织'],['组织']], 
        '成员', [['组织'],['组织']], 
        '创始人', [['组织'],['组织']], 
        '解散时间', [['组织'],['组织']], 
        '事件', [['组织'],['组织']],
    ], 
    '运输': [
        '位于', [['运输', '地理地区'],['地理地区']], 
        '创建时间', [['运输'],['时间']], 
        '线路', [['运输'],['运输']], 
        '开通时间', [['运输'],['时间']], 
        '途经', [['运输'],['地理地区']], 
        '面积', [['运输'],['度量']], 
        '别名', [['运输'],['运输']], 
        '长度', [['运输'],['度量']], 
        '宽度', [['运输'],['度量']], 
        '成就', [['运输'],['专业']], 
        '车站等级', [['运输'],['度量']]
    ], 
    '事件': [
        '参与者', [['事件'],['人物','组织']], 
        '发生地点', [['事件'],['地理地区']], 
        '发生时间', [['事件'],['时间']], 
        '别名', [['事件'],['事件']], 
        '赞助者', [['事件'],['人物','组织']], 
        '伤亡人数', [['事件'],['度量']], 
        '起因', [['事件'],[]], 
        '导致', [['事件'],[]], 
        '主办方', [['事件'],['组织']], 
        '所获奖项', [['事件'],['专业']], 
        '获胜者', [['事件'],['人物','组织']]
    ], 
    '天文对象': [
        '别名', [['天文对象类型'],['天文对象类型']], 
        '属于', [['天文对象类型'],['天文对象类型']], 
        '发现或发明时间', [['天文对象类型'],['时间']], 
        '发现者或发明者', [['天文对象类型'],['人物','组织']], 
        '名称由来', [['天文对象类型'],[]], 
        '绝对星等', [['天文对象类型'],['度量']], 
        '直径', [['天文对象类型'],['度量']], 
        '质量', [['天文对象类型'],['度量']]
    ], 
    '医学': [
        '症状', [['医学'],['医学']], 
        '别名', [['医学'],['医学']], 
        '发病部位', [['医学'],[]], 
        '可能后果', [['医学'],[]], 
        '病因', [['医学'],[]],
    ]
}
