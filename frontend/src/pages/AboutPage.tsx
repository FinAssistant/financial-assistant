import styled from 'styled-components'

const PageContainer = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: ${({ theme }) => theme.spacing.xl} 0;
`

const Title = styled.h1`
  font-size: ${({ theme }) => theme.fontSizes['3xl']};
  color: ${({ theme }) => theme.colors.primary.main};
  margin-bottom: ${({ theme }) => theme.spacing.lg};
  text-align: center;
`

const Content = styled.div`
  line-height: 1.7;
  color: ${({ theme }) => theme.colors.text.primary};
  
  p {
    margin-bottom: ${({ theme }) => theme.spacing.lg};
  }
  
  h2 {
    font-size: ${({ theme }) => theme.fontSizes.xl};
    margin: ${({ theme }) => theme.spacing.xl} 0 ${({ theme }) => theme.spacing.md};
    color: ${({ theme }) => theme.colors.text.primary};
  }
`

const TechStack = styled.ul`
  list-style: disc;
  margin-left: ${({ theme }) => theme.spacing.lg};
  margin-bottom: ${({ theme }) => theme.spacing.lg};
  
  li {
    margin-bottom: ${({ theme }) => theme.spacing.sm};
  }
`

function AboutPage() {
  return (
    <PageContainer>
      <Title>About AI Financial Assistant</Title>
      <Content>
        <p>
          AI Financial Assistant is a modern, full-stack application designed to help users 
          manage their finances with the power of artificial intelligence. Built with cutting-edge 
          technologies, it provides a secure and intuitive platform for financial management.
        </p>
        
        <h2>Technology Stack</h2>
        <p>This application is built using:</p>
        
        <TechStack>
          <li><strong>Frontend:</strong> React 18.2.x with TypeScript 5.3.x</li>
          <li><strong>Build Tool:</strong> Vite 5.0.x with esbuild bundling</li>
          <li><strong>Styling:</strong> Styled Components 6.1.x</li>
          <li><strong>State Management:</strong> Redux Toolkit 1.9.x</li>
          <li><strong>Backend:</strong> Python 3.11.x with FastAPI 0.104.x</li>
          <li><strong>Package Management:</strong> UV for Python dependencies</li>
          <li><strong>Containerization:</strong> Docker 24.x</li>
        </TechStack>
        
        <h2>Features</h2>
        <p>
          The application provides a comprehensive suite of financial management tools, 
          including expense tracking, budget planning, AI-powered insights, and secure 
          bank account integration through Plaid.
        </p>
        
        <p>
          Built with security and performance in mind, the application follows modern 
          development best practices and provides a responsive, user-friendly interface 
          across all devices.
        </p>
      </Content>
    </PageContainer>
  )
}

export default AboutPage