import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Input, Button, List, Card, Tag, Spin, Empty, Select, Typography, Space } from 'antd'
import { SearchOutlined, DatabaseOutlined } from '@ant-design/icons'
import { queryRag, listLibraries, Library, QueryResult } from '../services/api'

const { Title } = Typography

export default function Chat() {
  const { libraryId } = useParams<{ libraryId?: string }>()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<QueryResult[]>([])
  const [libraries, setLibraries] = useState<Library[]>([])
  const [selectedLib, setSelectedLib] = useState<string | undefined>(libraryId)

  useEffect(() => {
    listLibraries().then(data => {
      setLibraries(data.libraries || [])
    }).catch(console.error)
  }, [])

  useEffect(() => {
    setSelectedLib(libraryId)
  }, [libraryId])

  const handleSearch = async () => {
    if (!query.trim()) return

    setLoading(true)
    try {
      const data = await queryRag({
        query: query.trim(),
        library_id: selectedLib,
        top_k: 10
      })
      setResults(data.results || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSearch()
    }
  }

  const handleLibChange = (value: string | undefined) => {
    setSelectedLib(value)
    if (value) {
      navigate(`/chat/${value}`)
    } else {
      navigate('/chat')
    }
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <Title level={3}>文档查询</Title>

      <div style={{ marginBottom: 16 }}>
        <Select
          style={{ width: 300 }}
          placeholder="选择知识库（可选）"
          allowClear
          value={selectedLib}
          onChange={handleLibChange}
          options={[
            { value: '', label: '全部知识库' },
            ...libraries.map(lib => ({ value: lib.id, label: lib.name }))
          ]}
        />
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        <Input
          size="large"
          placeholder="输入问题进行搜索..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          prefix={<SearchOutlined />}
          style={{ flex: 1 }}
        />
        <Button type="primary" size="large" onClick={handleSearch} loading={loading}>
          查询
        </Button>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>正在检索...</div>
        </div>
      )}

      {!loading && results.length === 0 && query && (
        <Empty description="未找到相关内容" />
      )}

      {!loading && results.length > 0 && (
        <List
          locale={{ emptyText: '输入问题开始查询' }}
          dataSource={results}
          renderItem={(item, index) => (
            <List.Item style={{ display: 'block', padding: '16px 0' }}>
              <Card
                size="small"
                title={
                  <Space>
                    <DatabaseOutlined />
                    <span>{item.source}</span>
                    <Tag color={getScoreColor(item.score)}>
                      {Math.round(item.score * 100)}%
                    </Tag>
                  </Space>
                }
                style={{ background: '#fafafa' }}
              >
                <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                  {item.content}
                </div>
              </Card>
            </List.Item>
          )}
        />
      )}
    </div>
  )
}

function getScoreColor(score: number): string {
  if (score >= 0.9) return 'green'
  if (score >= 0.7) return 'blue'
  if (score >= 0.5) return 'orange'
  return 'red'
}
