// Mock 数据

// 登录用户信息
export const mockUser = {
  id: 1,
  username: '测试用户',
  email: 'test@example.com',
  role: 'user',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
}

// 会话列表
export const mockSessions = [
  {
    session_id: 'session_123',
    title: '工作压力导致的焦虑',
    last_message: '谢谢，我感觉好多了',
    created_at: '2024-03-20T10:00:00Z',
    emotion_label: '焦虑',
    automatic_thoughts: ['我什么都做不好', '同事们都在针对我'],
    message_count: 15
  },
  {
    session_id: 'session_456',
    title: '人际关系困扰',
    last_message: '我会尝试你的建议',
    created_at: '2024-03-19T15:30:00Z',
    emotion_label: '抑郁',
    automatic_thoughts: ['没有人理解我', '我很孤独'],
    message_count: 12
  },
  {
    session_id: 'session_789',
    title: '学业压力',
    last_message: '好的，我知道了',
    created_at: '2024-03-18T09:15:00Z',
    emotion_label: '压力',
    automatic_thoughts: ['我考不上大学', '我让父母失望了'],
    message_count: 8
  }
]

// 对话历史
export const mockDialogueHistory = {
  dialogues: [
    {
      id: 1,
      user_id: 1,
      session_id: 'session_123',
      role: 'user',
      content: '我最近工作压力很大，感觉喘不过气来',
      four_dim_intensity: 8.5,
      four_dim_hedonic: '负性',
      four_dim_tension: '高',
      four_dim_complexity: '复杂',
      is_valuable: true,
      created_at: '2024-03-20T10:00:00Z'
    },
    {
      id: 2,
      user_id: 1,
      session_id: 'session_123',
      role: 'assistant',
      content: '听起来你现在承受着很大的工作压力，能具体说说是什么让你感到压力吗？',
      four_dim_intensity: 0,
      four_dim_hedonic: '中性',
      four_dim_tension: '低',
      four_dim_complexity: '简单',
      is_valuable: false,
      created_at: '2024-03-20T10:01:00Z'
    },
    {
      id: 3,
      user_id: 1,
      session_id: 'session_123',
      role: 'user',
      content: '项目 deadline 快到了，但是有很多问题还没解决，我担心会完不成',
      four_dim_intensity: 9.0,
      four_dim_hedonic: '负性',
      four_dim_tension: '高',
      four_dim_complexity: '复杂',
      is_valuable: true,
      created_at: '2024-03-20T10:02:00Z'
    }
  ]
}

// 记录报告
export const mockRecordReport = {
  record_id: 'record_123',
  session_id: 'session_123',
  user_id: 1,
  duration: 120.5,
  situation: '工作压力大，项目 deadline 临近，担心无法完成任务',
  automatic_thoughts: ['我什么都做不好', '同事们都在针对我', '我会被开除'],
  emotions: [
    { type: '焦虑', intensity: 9, description: '对工作任务的担忧' },
    { type: '压力', intensity: 8, description: '来自 deadline 的压力' },
    { type: '恐惧', intensity: 7, description: '对失败的恐惧' }
  ],
  physical_sensations: ['头痛', '失眠', '胃部不适'],
  summary: '来访者因工作压力过大导致焦虑和压力，伴有身体不适症状',
  timestamp: '2024-03-20T10:30:00Z'
}

// 分析报告
export const mockAnalysisReport = {
  report_id: 'analysis_123',
  record_id: 'record_123',
  content: {
    cbt_summary: '来访者存在明显的灾难化思维，将工作中的困难过度放大，导致情绪压力。建议使用认知重构技术，帮助来访者识别和挑战负面思维模式。',
    tcm_summary: '从中医角度看，来访者因长期压力导致肝气郁结，气血不畅，从而出现头痛、失眠等症状。建议疏肝理气，调理气血。',
    four_dim_data: {
      intensities: [8.5, 9.0, 8.0, 7.5, 7.0],
      hedonics: ['负性', '负性', '负性', '中性', '中性'],
      tensions: ['高', '高', '中', '中', '低'],
      complexities: ['复杂', '复杂', '中等', '中等', '简单'],
      timestamps: ['10:00', '10:02', '10:05', '10:10', '10:15']
    },
    emotion_trend: {
      labels: ['焦虑', '压力', '恐惧', '沮丧', '担忧'],
      values: [9, 8, 7, 6, 5]
    }
  },
  timestamp: '2024-03-20T10:35:00Z'
}

// 调理报告
export const mockTreatmentReport = {
  report_id: 'treatment_123',
  analysis_id: 'analysis_123',
  therapy_plan: '1. 认知重构：识别并挑战负面思维模式\n2. 放松训练：每天进行10分钟深呼吸练习\n3. 时间管理：制定合理的工作计划，分解任务\n4. 运动：每天进行30分钟有氧运动\n5. 睡眠：保持规律的作息时间',
  therapist_summary: '通过认知行为疗法和生活方式调整，帮助来访者缓解工作压力，改善情绪状态。建议来访者坚持练习，并定期进行情绪监测。',
  cbt_assignments: [
    '每天记录3件完成的工作，增强成就感',
    '当出现负面思维时，写下证据支持和反驳的理由',
    '每周安排2-3次放松训练时间'
  ],
  timestamp: '2024-03-20T10:40:00Z'
}

// 情绪日记数据
export const mockMoodEntries = [
  {
    id: 1,
    user_id: 1,
    entry_date: '2024-03-20',
    mood_label: '焦虑',
    signature_text: '今天工作压力很大，但我会坚持下去',
    four_dim_intensity: 8.0,
    four_dim_hedonic: '负性',
    four_dim_tension: '高',
    four_dim_complexity: '复杂',
    created_at: '2024-03-20T20:00:00Z'
  },
  {
    id: 2,
    user_id: 1,
    entry_date: '2024-03-19',
    mood_label: '抑郁',
    signature_text: '今天感觉很孤独，没有人理解我',
    four_dim_intensity: 7.5,
    four_dim_hedonic: '负性',
    four_dim_tension: '中',
    four_dim_complexity: '中等',
    created_at: '2024-03-19T20:30:00Z'
  },
  {
    id: 3,
    user_id: 1,
    entry_date: '2024-03-18',
    mood_label: '平静',
    signature_text: '今天比较平静，完成了一些工作',
    four_dim_intensity: 4.0,
    four_dim_hedonic: '中性',
    four_dim_tension: '低',
    four_dim_complexity: '简单',
    created_at: '2024-03-18T19:45:00Z'
  }
]

// 日历数据
export const mockCalendarData = {
  days: [
    { date: '2024-03-01', mood_label: '平静', signature: '新的开始' },
    { date: '2024-03-05', mood_label: '开心', signature: '完成了一个项目' },
    { date: '2024-03-10', mood_label: '焦虑', signature: '工作压力大' },
    { date: '2024-03-15', mood_label: '抑郁', signature: '感到孤独' },
    { date: '2024-03-20', mood_label: '焦虑', signature: '工作压力很大' }
  ]
}

// 情绪趋势数据
export const mockMoodTrend = {
  dates: ['2024-03-15', '2024-03-16', '2024-03-17', '2024-03-18', '2024-03-19', '2024-03-20'],
  intensities: [7.5, 7.0, 6.5, 4.0, 7.5, 8.0],
  labels: ['抑郁', '抑郁', '焦虑', '平静', '抑郁', '焦虑']
}

// 问卷列表
export const mockQuestionnaires = [
  {
    id: 1,
    name: 'PHQ-9 抑郁量表',
    description: '用于评估抑郁症状的严重程度'
  },
  {
    id: 2,
    name: 'GAD-7 焦虑量表',
    description: '用于评估焦虑症状的严重程度'
  },
  {
    id: 3,
    name: 'SDS 抑郁自评量表',
    description: '用于自我评估抑郁程度'
  }
]

// 问卷详情
export const mockQuestionnaireDetail = {
  id: 1,
  name: 'PHQ-9 抑郁量表',
  description: '用于评估抑郁症状的严重程度',
  questions_json: [
    {
      id: 1,
      question: '做事时提不起劲或没有兴趣',
      options: [
        { value: 0, label: '完全没有' },
        { value: 1, label: '有几天' },
        { value: 2, label: '一半以上天数' },
        { value: 3, label: '几乎每天' }
      ]
    },
    {
      id: 2,
      question: '感到心情低落、沮丧或绝望',
      options: [
        { value: 0, label: '完全没有' },
        { value: 1, label: '有几天' },
        { value: 2, label: '一半以上天数' },
        { value: 3, label: '几乎每天' }
      ]
    },
    {
      id: 3,
      question: '入睡困难、睡不安稳或睡太多',
      options: [
        { value: 0, label: '完全没有' },
        { value: 1, label: '有几天' },
        { value: 2, label: '一半以上天数' },
        { value: 3, label: '几乎每天' }
      ]
    }
  ],
  scoring_rule: {
    ranges: [
      { min: 0, max: 4, severity: '无抑郁' },
      { min: 5, max: 9, severity: '轻度抑郁' },
      { min: 10, max: 14, severity: '中度抑郁' },
      { min: 15, max: 27, severity: '重度抑郁' }
    ]
  }
}

// 预警列表
export const mockAlerts = [
  {
    id: 1,
    user_id: 1,
    alert_type: 'session',
    alert_level: 'warning',
    message: '您最近的对话中情绪强度持续较高，建议关注情绪变化',
    trigger_data: {
      session_id: 'session_123',
      emotion_intensity: 8.5,
      trend: '上升'
    },
    is_acknowledged: false,
    created_at: '2024-03-20T11:00:00Z'
  },
  {
    id: 2,
    user_id: 1,
    alert_type: 'trend',
    alert_level: 'danger',
    message: '您近7天的情绪记录显示持续负性情绪，建议寻求专业帮助',
    trigger_data: {
      average_intensity: 7.8,
      negative_days: 6,
      trend: '持续负性'
    },
    is_acknowledged: false,
    created_at: '2024-03-20T09:00:00Z'
  }
]

// 管理员用户列表
export const mockAdminUsers = {
  users: [
    {
      id: 1,
      username: '测试用户',
      email: 'test@example.com',
      role: 'user',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: 2,
      username: '管理员',
      email: 'admin@example.com',
      role: 'admin',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: 3,
      username: '超级管理员',
      email: 'superadmin@example.com',
      role: 'super_admin',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z'
    }
  ],
  total: 3
}

// 策略库列表
export const mockStrategies = {
  strategies: [
    {
      id: 1,
      intensity_level: '高',
      hedonic: '负性',
      tension: '高',
      complexity: '复杂',
      fusion_mode: '认知行为+中医',
      cbt_techniques: '认知重构、放松训练',
      tcm_methods: '疏肝理气、安神定志',
      strategy_content: '通过认知重构挑战负面思维，同时使用中医方法调理身体',
      example: '针对工作压力大的来访者，先进行认知重构，然后建议服用逍遥丸调理肝气',
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: 2,
      intensity_level: '中',
      hedonic: '中性',
      tension: '中',
      complexity: '中等',
      fusion_mode: '认知行为',
      cbt_techniques: '问题解决、时间管理',
      tcm_methods: '平衡阴阳',
      strategy_content: '通过问题解决和时间管理技术，帮助来访者应对日常压力',
      example: '针对学业压力的学生，教授时间管理技巧，帮助制定合理的学习计划',
      created_at: '2024-01-01T00:00:00Z'
    }
  ],
  total: 2
}

// 管理员操作日志
export const mockAdminLogs = {
  logs: [
    {
      id: 1,
      admin_id: 3,
      action: 'create_user',
      target: '测试用户',
      details: '创建了新用户：测试用户',
      ip_address: '127.0.0.1',
      created_at: '2024-03-20T10:00:00Z'
    },
    {
      id: 2,
      admin_id: 3,
      action: 'update_strategy',
      target: '策略1',
      details: '更新了策略：认知行为+中医',
      ip_address: '127.0.0.1',
      created_at: '2024-03-19T15:30:00Z'
    }
  ],
  total: 2
}

export default {
  mockUser,
  mockSessions,
  mockDialogueHistory,
  mockRecordReport,
  mockAnalysisReport,
  mockTreatmentReport,
  mockMoodEntries,
  mockCalendarData,
  mockMoodTrend,
  mockQuestionnaires,
  mockQuestionnaireDetail,
  mockAlerts,
  mockAdminUsers,
  mockStrategies,
  mockAdminLogs
}
