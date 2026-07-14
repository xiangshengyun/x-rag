import { Routes, Route, Link } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import { DatabaseOutlined, SearchOutlined } from '@ant-design/icons'
import Libraries from './pages/Libraries'
import Chat from './pages/Chat'
import './App.css'

const { Header, Content } = Layout

function App() {
  return (
    <Layout className="layout">
      <Header style={{ display: 'flex', alignItems: 'center' }}>
        <div className="logo" style={{ color: 'white', fontSize: 20, fontWeight: 'bold', marginRight: 40 }}>
          X-RAG
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          defaultSelectedKeys={['libraries']}
          style={{ flex: 1 }}
          items={[
            {
              key: 'libraries',
              icon: <DatabaseOutlined />,
              label: <Link to="/">知识库</Link>,
            },
            {
              key: 'chat',
              icon: <SearchOutlined />,
              label: <Link to="/chat">查询</Link>,
            },
          ]}
        />
      </Header>
      <Content style={{ padding: '0 50px', minHeight: 'calc(100vh - 64px)' }}>
        <div className="content">
          <Routes>
            <Route path="/" element={<Libraries />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/chat/:libraryId" element={<Chat />} />
          </Routes>
        </div>
      </Content>
    </Layout>
  )
}

export default App
