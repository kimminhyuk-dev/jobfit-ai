import type { Analysis, Skill } from '../types';

export const mockSkills: Skill[] = [
  { name: 'React', user: 92, market: 85, status: 'strong' },
  { name: 'TypeScript', user: 84, market: 80, status: 'strong' },
  { name: 'CSS / Tailwind', user: 78, market: 70, status: 'strong' },
  { name: 'Next.js', user: 65, market: 75, status: 'gap' },
  { name: 'GraphQL', user: 32, market: 60, status: 'weak' },
  { name: 'Testing (Jest/RTL)', user: 48, market: 65, status: 'gap' },
];

export const mockAnalysis: Analysis = {
  strengths: [
    {
      title: '탄탄한 React 생태계 경험',
      detail: '3년 이상의 React 실무와 Next.js 프로젝트 2건이 경쟁 지원자 대비 상위 15%에 해당합니다.',
    },
    {
      title: '디자인 시스템 구축 이력',
      detail: 'Storybook 기반 컴포넌트 라이브러리 운영 경험은 시니어 직무에서 강력한 차별점입니다.',
    },
    {
      title: '명확한 임팩트 서술',
      detail: '"전환율 18% 개선" 등 정량 지표가 구체적으로 기술되어 있어 추천도가 높습니다.',
    },
  ],
  weaknesses: [
    {
      title: '백엔드 협업 경험 부족',
      detail: 'API 설계나 BFF 레이어 관련 서술이 약합니다. 풀스택 포지션 매칭 점수가 낮아지는 원인입니다.',
    },
    {
      title: '테스트 자동화 경험 미언급',
      detail: '대부분의 시니어 채용공고에서 Jest/RTL 또는 Cypress 경험을 요구합니다.',
    },
  ],
  recommendations: [
    {
      title: 'GraphQL 학습 후 사이드 프로젝트',
      detail: 'Apollo Client 기반 작은 프로젝트를 추가하면 매칭 점수가 평균 +6점 상승할 것으로 예상됩니다.',
      impact: '+6점',
    },
    {
      title: '"성과" 섹션을 최상단으로',
      detail: '리쿠르터의 평균 이력서 검토 시간은 23초입니다. 첫 화면에 임팩트 지표를 배치하세요.',
      impact: '+3점',
    },
    {
      title: '협업 키워드 보강',
      detail: '"백엔드 엔지니어 2인과 협업", "디자이너와 위클리 동기화" 같은 협업 맥락을 추가하세요.',
      impact: '+4점',
    },
  ],
};
