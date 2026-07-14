import { useState, useEffect, useRef } from 'react'
import { Table, Button, Modal, Form, Input, Space, message, Popconfirm, Progress, Tag, List, Typography, Slider, InputNumber } from 'antd'
import { PlusOutlined, DeleteOutlined, SyncOutlined, FolderOpenOutlined, FileTextOutlined, SettingOutlined } from '@ant-design/icons'
import { listLibraries, createLibrary, deleteLibrary, scanLibrary, getScanProgress, getLibraryChunks, getChunkConfig, updateChunkConfig, Library, ScanProgress } from '../services/api'

const { TextArea } = Input
const { Text } = Typography

export default function Libraries() {
  const [libraries, setLibraries] = useState<Library[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [scanningLib, setScanningLib] = useState<string | null>(null)
  const [scanProgress, setScanProgress] = useState<ScanProgress | null>(null)
  const [chunksModalOpen, setChunksModalOpen] = useState(false)
  const [chunksLoading, setChunksLoading] = useState(false)
  const [chunks, setChunks] = useState<any[]>([])
  const [currentLibrary, setCurrentLibrary] = useState<Library | null>(null)
  const [configModalOpen, setConfigModalOpen] = useState(false)
  const [chunkSize, setChunkSize] = useState(500)
  const [chunkOverlap, setChunkOverlap] = useState(50)
  const [configLoading, setConfigLoading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const loadLibraries = async () => {
    setLoading(true)
    try {
      const data = await listLibraries()
      setLibraries(data.libraries || [])
    } catch (e) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const loadChunkConfig = async () => {
    try {
      const data = await getChunkConfig()
      setChunkSize(data.chunk_size)
      setChunkOverlap(data.chunk_overlap)
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    loadLibraries()
  }, [])

  // 轮询扫描进度
  useEffect(() => {
    if (!scanningLib) return

    const interval = setInterval(async () => {
      try {
        const progress = await getScanProgress(scanningLib)
        setScanProgress(progress)
        if (progress.status === 'completed' || progress.status === 'failed') {
          setScanningLib(null)
          clearInterval(interval)
          loadLibraries()
        }
      } catch (e) {
        console.error(e)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [scanningLib])

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      await createLibrary(values)
      message.success('创建成功')
      setModalOpen(false)
      form.resetFields()
      loadLibraries()
    } catch (e: any) {
      if (e?.response?.data?.detail) {
        message.error(e.response.data.detail)
      } else {
        message.error('创建失败')
      }
    }
  }

  const handleDelete = async (libraryId: string) => {
    try {
      await deleteLibrary(libraryId)
      message.success('删除成功')
      loadLibraries()
    } catch (e) {
      message.error('删除失败')
    }
  }

  const handleScan = async (libraryId: string) => {
    setScanningLib(libraryId)
    try {
      await scanLibrary(libraryId)
    } catch (e) {
      setScanningLib(null)
      message.error('扫描失败')
    }
  }

  const handleShowChunks = async (library: Library) => {
    setCurrentLibrary(library)
    setChunksModalOpen(true)
    setChunksLoading(true)
    try {
      const data = await getLibraryChunks(library.id)
      setChunks(data.chunks || [])
    } catch (e) {
      message.error('获取分块失败')
    } finally {
      setChunksLoading(false)
    }
  }

  const handleOpenConfig = async () => {
    await loadChunkConfig()
    setConfigModalOpen(true)
  }

  const handleSaveConfig = async () => {
    setConfigLoading(true)
    try {
      await updateChunkConfig({ chunk_size: chunkSize, chunk_overlap: chunkOverlap })
      message.success('配置已保存')
      setConfigModalOpen(false)
    } catch (e) {
      message.error('保存失败')
    } finally {
      setConfigLoading(false)
    }
  }

  const handleFolderSelect = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      const file = files[0]
      const relativePath = (file as any).webkitRelativePath || ''
      const folderPath = relativePath.split('/')[0] || ''
      const fullPath = (file as any).path || folderPath

      if (fullPath) {
        form.setFieldsValue({ source_path: fullPath })
      } else {
        message.warning('无法获取文件夹路径，请手动输入')
      }
    }
    e.target.value = ''
  }

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '路径',
      dataIndex: 'source_path',
      key: 'source_path',
      ellipsis: true,
    },
    {
      title: '文档数',
      dataIndex: 'document_count',
      key: 'document_count',
      width: 100,
    },
    {
      title: '分块数',
      dataIndex: 'chunk_count',
      key: 'chunk_count',
      width: 100,
      render: (count: number, record: Library) =>
        count > 0 ? (
          <Button type="link" onClick={() => handleShowChunks(record)}>
            {count}
          </Button>
        ) : (
          <Text type="secondary">0</Text>
        ),
    },
    {
      title: '状态',
      key: 'status',
      width: 120,
      render: (_: any, record: Library) => {
        if (scanningLib === record.id && scanProgress) {
          const statusMap: Record<string, { color: string; text: string }> = {
            scanning: { color: 'blue', text: '扫描中' },
            embedding: { color: 'orange', text: '向量化' },
            completed: { color: 'green', text: '完成' },
            failed: { color: 'red', text: '失败' },
          }
          const s = statusMap[scanProgress.status] || { color: 'default', text: scanProgress.status }
          return <Tag color={s.color}>{s.text}</Tag>
        }
        return record.chunk_count > 0 ? <Tag color="green">已索引</Tag> : <Tag>未索引</Tag>
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: Library) => (
        <Space>
          <Button
            type="link"
            icon={<SyncOutlined spin={scanningLib === record.id} />}
            onClick={() => handleScan(record.id)}
            disabled={scanningLib === record.id}
          >
            {record.chunk_count > 0 ? '重建索引' : '建立索引'}
          </Button>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2>知识库管理</h2>
        <Space>
          <Button icon={<SettingOutlined />} onClick={handleOpenConfig}>
            分块策略
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            添加知识库
          </Button>
        </Space>
      </div>

      {scanningLib && scanProgress && (
        <div style={{ marginBottom: 16, padding: 16, background: '#f5f5f5', borderRadius: 8 }}>
          <div style={{ marginBottom: 8 }}>{scanProgress.message}</div>
          <Progress
            percent={Math.round((scanProgress.processed_files / Math.max(scanProgress.total_files, 1)) * 100)}
            status={scanProgress.status === 'failed' ? 'exception' : 'active'}
          />
        </div>
      )}

      <Table
        columns={columns}
        dataSource={libraries}
        rowKey="id"
        loading={loading}
        locale={{ emptyText: '暂无知识库，点击添加创建一个' }}
      />

      {/* 添加知识库弹窗 */}
      <Modal
        title="添加知识库"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => {
          setModalOpen(false)
          form.resetFields()
        }}
        okText="创建"
        cancelText="取消"
      >
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          webkitdirectory="webkitdirectory"
          onChange={handleFileChange}
        />

        <Form form={form} layout="vertical" style={{ marginTop: 20 }}>
          <Form.Item
            name="name"
            label="知识库名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="例如：产品文档" />
          </Form.Item>
          <Form.Item
            name="source_path"
            label="文件夹路径"
            rules={[{ required: true, message: '请输入或选择文件夹路径' }]}
            extra="支持 PDF、Markdown、TXT 文件"
          >
            <Input
              placeholder="例如：D:\docs\project"
              prefix={<FolderOpenOutlined />}
              suffix={
                <Button size="small" onClick={handleFolderSelect}>
                  选择文件夹
                </Button>
              }
            />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="可选描述" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 分块详情弹窗 */}
      <Modal
        title={`分块详情 - ${currentLibrary?.name || ''}`}
        open={chunksModalOpen}
        onCancel={() => setChunksModalOpen(false)}
        footer={null}
        width={800}
      >
        <List
          loading={chunksLoading}
          dataSource={chunks}
          locale={{ emptyText: '暂无分块' }}
          style={{ maxHeight: '60vh', overflowY: 'auto' }}
          renderItem={(item: any, index: number) => (
            <List.Item style={{ display: 'block', padding: '12px 0' }}>
              <div style={{ marginBottom: 8 }}>
                <FileTextOutlined style={{ marginRight: 8 }} />
                <Text type="secondary">
                  {item.metadata?.file_name || '未知文件'} (分块 {index + 1})
                </Text>
              </div>
              <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, background: '#f5f5f5', padding: 12, borderRadius: 4 }}>
                {item.content}
              </div>
            </List.Item>
          )}
        />
      </Modal>

      {/* 分块策略配置弹窗 */}
      <Modal
        title="分块策略配置"
        open={configModalOpen}
        onOk={handleSaveConfig}
        onCancel={() => setConfigModalOpen(false)}
        okText="保存"
        cancelText="取消"
        confirmLoading={configLoading}
      >
        <div style={{ marginTop: 20 }}>
          <Text strong>分块大小: {chunkSize}</Text>
          <Slider
            min={100}
            max={2000}
            step={50}
            value={chunkSize}
            onChange={setChunkSize}
            style={{ marginBottom: 24 }}
          />

          <Text strong>分块重叠: {chunkOverlap}</Text>
          <Slider
            min={0}
            max={500}
            step={10}
            value={chunkOverlap}
            onChange={setChunkOverlap}
          />

          <div style={{ marginTop: 16, color: '#888', fontSize: 12 }}>
            <p>• 分块大小：每个文本块的最大字符数</p>
            <p>• 分块重叠：相邻块之间的重叠字符数，用于保持上下文连贯性</p>
            <p style={{ color: '#faad14' }}>⚠️ 修改配置后，需要重新扫描才能生效</p>
          </div>
        </div>
      </Modal>
    </div>
  )
}
