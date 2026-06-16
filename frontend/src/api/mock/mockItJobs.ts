export interface MockJobItem {
  job_id: number;
  source: string;
  source_job_id: string;
  source_url: string | null;
  company_name: string;
  title: string;
  location: string;
  location_address: string;
  career_level: string;
  min_career_years: number | null;
  max_career_years: number | null;
  education: string;
  employment_type: string;
  industry: string;
  work_schedule: string;
  ncs_category: string;
  salary_type: string;
  salary_text: string;
  min_salary: number;
  max_salary: number;
  tech_stack: string[];
  description: string;
  benefits: string[];
  headcount: number | null;
  job_category: string;
  posted_at: string;
  deadline: string;
  status: string;
  data_source: string;
  collected_at: string;
}

type CareerType = '신입' | '경력';

interface JobTemplate {
  category: string;
  title: string;
  techStack: string[];
  industry: string;
  ncsCategory: string;
  juniorSalary: [number, number];
  seniorSalary: [number, number];
}

export const MOCK_JOB_CATEGORIES = [
  '전체',
  '백엔드',
  '프론트엔드',
  '풀스택',
  '모바일',
  '데이터',
  'AI·ML',
  'DevOps·SRE',
  'QA·보안',
  '게임',
  'ERP·SI',
];

const COMPANIES = [
  '넥스트커머스',
  '브릿지테크',
  '핀업랩스',
  '클라우드링크',
  '데이터그로브',
  '모션페이',
  '픽셀스튜디오',
  '루트소프트',
  '코어플랫폼',
  '인사이트웍스',
  '그린에너지IT',
  '메디플로우',
  '에듀코어',
  '오토메이션랩',
  '마켓웨이브',
  '시큐어넷',
  '게임포지',
  '스마트팩토리온',
  '웰니스앱스',
  '비즈온클라우드',
];

const LOCATIONS = [
  ['서울 강남구', '서울특별시 강남구 테헤란로 123'],
  ['서울 구로구', '서울특별시 구로구 디지털로 300'],
  ['서울 마포구', '서울특별시 마포구 월드컵북로 45'],
  ['서울 금천구', '서울특별시 금천구 가산디지털1로 88'],
  ['경기 성남시', '경기도 성남시 분당구 판교역로 235'],
  ['경기 수원시', '경기도 수원시 영통구 광교로 156'],
  ['부산 해운대구', '부산광역시 해운대구 센텀중앙로 90'],
  ['대전 유성구', '대전광역시 유성구 대학로 99'],
];

const BENEFIT_SETS = [
  ['유연근무', '점심 식사 지원', '성과급', '연차제도'],
  ['재택근무 가능', '장비 지원', '교육비 지원', '건강검진'],
  ['자율출퇴근', '스톡옵션', '도서구입비', '컨퍼런스 참가 지원'],
  ['4대보험', '퇴직금', '경조사 지원', '명절선물'],
];

const TEMPLATES: JobTemplate[] = [
  {
    category: '백엔드',
    title: '백엔드 개발자',
    techStack: ['Java', 'Spring Boot', 'JPA', 'MySQL', 'Redis'],
    industry: '솔루션·SI·CRM·ERP',
    ncsCategory: '정보통신 > 소프트웨어개발',
    juniorSalary: [3200, 4200],
    seniorSalary: [5200, 8200],
  },
  {
    category: '프론트엔드',
    title: '프론트엔드 개발자',
    techStack: ['React', 'TypeScript', 'Next.js', 'TanStack Query'],
    industry: '포털·인터넷·콘텐츠',
    ncsCategory: '정보통신 > 응용SW개발',
    juniorSalary: [3100, 4300],
    seniorSalary: [5000, 7800],
  },
  {
    category: '풀스택',
    title: '풀스택 웹개발자',
    techStack: ['Node.js', 'React', 'PostgreSQL', 'AWS'],
    industry: '소프트웨어개발',
    ncsCategory: '정보통신 > 소프트웨어개발',
    juniorSalary: [3300, 4500],
    seniorSalary: [5400, 8500],
  },
  {
    category: '모바일',
    title: '모바일 앱개발자',
    techStack: ['Kotlin', 'Swift', 'Flutter', 'Firebase'],
    industry: '모바일·APP',
    ncsCategory: '정보통신 > 응용SW개발',
    juniorSalary: [3200, 4400],
    seniorSalary: [5200, 8200],
  },
  {
    category: '데이터',
    title: '데이터 엔지니어',
    techStack: ['Python', 'SQL', 'Airflow', 'Spark', 'dbt'],
    industry: '데이터·AI',
    ncsCategory: '정보통신 > 데이터베이스·빅데이터',
    juniorSalary: [3400, 4700],
    seniorSalary: [5800, 9200],
  },
  {
    category: 'AI·ML',
    title: 'AI 엔지니어',
    techStack: ['Python', 'PyTorch', 'Transformers', 'MLOps'],
    industry: '인공지능·빅데이터',
    ncsCategory: '정보통신 > 인공지능',
    juniorSalary: [3600, 5000],
    seniorSalary: [6500, 11000],
  },
  {
    category: 'DevOps·SRE',
    title: 'DevOps 엔지니어',
    techStack: ['AWS', 'Docker', 'Kubernetes', 'Terraform', 'GitHub Actions'],
    industry: '클라우드·인프라',
    ncsCategory: '정보통신 > IT시스템관리',
    juniorSalary: [3400, 4800],
    seniorSalary: [6000, 9800],
  },
  {
    category: 'QA·보안',
    title: 'QA·보안 엔지니어',
    techStack: ['Selenium', 'JMeter', 'Python', 'OWASP', 'Burp Suite'],
    industry: '정보보안·품질관리',
    ncsCategory: '정보통신 > 정보보안',
    juniorSalary: [3100, 4300],
    seniorSalary: [5200, 8600],
  },
  {
    category: '게임',
    title: '게임 서버 개발자',
    techStack: ['C++', 'C#', 'Unity', 'Unreal', 'Redis'],
    industry: '게임·애니메이션',
    ncsCategory: '문화예술·디자인 > 게임제작',
    juniorSalary: [3300, 4700],
    seniorSalary: [5800, 9500],
  },
  {
    category: 'ERP·SI',
    title: 'ERP·SI 개발자',
    techStack: ['Java', 'Spring', 'Oracle', 'Nexacro', 'SAP'],
    industry: '솔루션·SI·ERP',
    ncsCategory: '정보통신 > 응용SW개발',
    juniorSalary: [3000, 4100],
    seniorSalary: [4800, 7600],
  },
];

function createJob(index: number, careerType: CareerType): MockJobItem {
  const template = TEMPLATES[(index - 1) % TEMPLATES.length];
  const company = COMPANIES[(index - 1) % COMPANIES.length];
  const [location, address] = LOCATIONS[(index - 1) % LOCATIONS.length];
  const [minSalary, maxSalary] =
    careerType === '신입' ? template.juniorSalary : template.seniorSalary;
  const minCareer = careerType === '신입' ? null : 2 + (index % 6);
  const postedDay = (index % 20) + 1;
  const deadlineDay = (index % 24) + 1;
  const headcount = careerType === '신입' ? 3 + (index % 6) : 1 + (index % 4);
  const jobNo = careerType === '신입' ? index : index + 50;

  return {
    job_id: 2000 + jobNo,
    source: 'WORK24',
    source_job_id: `WORK24-MOCK-${2000 + jobNo}`,
    source_url: null,
    company_name: company,
    title: `${careerType} ${template.title} (${template.techStack.slice(0, 2).join('/')})`,
    location,
    location_address: `${address} ${jobNo}층`,
    career_level: careerType === '신입' ? '신입' : `경력 ${minCareer}년↑`,
    min_career_years: minCareer,
    max_career_years: null,
    education: careerType === '신입' ? '초대졸 이상' : '학력무관',
    employment_type: '정규직',
    industry: template.industry,
    work_schedule: index % 3 === 0 ? '주 5일·하이브리드' : '주 5일·유연근무',
    ncs_category: template.ncsCategory,
    salary_type: 'Y',
    salary_text: `연봉 ${minSalary.toLocaleString()}~${maxSalary.toLocaleString()}만원`,
    min_salary: minSalary,
    max_salary: maxSalary,
    tech_stack: template.techStack,
    description:
      `${company}에서 ${careerType} ${template.title}를 모집합니다. ` +
      `${template.techStack.join(', ')} 기반으로 서비스 기능 개발, 운영 자동화, ` +
      '성능 개선, 협업 프로세스 개선을 함께 담당합니다. 사람인·잡코리아식 공고처럼 ' +
      '직무, 기술스택, 경력 조건, 복지 정보를 한눈에 확인할 수 있도록 구성한 데모 데이터입니다.',
    benefits: BENEFIT_SETS[(index - 1) % BENEFIT_SETS.length],
    headcount,
    job_category: template.category,
    posted_at: `2026-05-${String(postedDay).padStart(2, '0')}T09:00:00+09:00`,
    deadline: `2026-06-${String(deadlineDay).padStart(2, '0')}T23:59:59+09:00`,
    status: 'OPEN',
    data_source: 'MOCK',
    collected_at: '2026-06-15T09:00:00+09:00',
  };
}

const juniorJobs = Array.from({ length: 50 }, (_, i) => createJob(i + 1, '신입'));
const seniorJobs = Array.from({ length: 50 }, (_, i) => createJob(i + 1, '경력'));

export const mockItJobs: MockJobItem[] = [...juniorJobs, ...seniorJobs];
