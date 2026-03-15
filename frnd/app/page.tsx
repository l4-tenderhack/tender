import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col gap-8 animate-in fade-in duration-700">
      {/* Hero Section */}
      <section className="bg-white border border-border-portal rounded-lg p-10 shadow-sm relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-64 h-64 bg-portal-blue/5 rounded-full -mr-20 -mt-20 blur-3xl transition-transform group-hover:scale-110 duration-1000" />
        <div className="relative z-10 max-w-2xl">
          <div className="flex items-center gap-2 mb-4">
            <span className="bg-portal-blue/10 text-portal-blue px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase">Проект Tender Hack</span>
            <span className="w-1.5 h-1.5 rounded-full bg-portal-green" />
          </div>
          <h1 className="text-4xl font-black text-text-main mb-6 leading-tight tracking-tight">
            Интеллектуальный поиск <br />
            <span className="text-portal-blue">и обоснование закупок</span>
          </h1>
          <p className="text-lg text-text-muted mb-8 leading-relaxed font-medium">
            Технологическое расширение для автоматизации расчетов НМЦК на базе векторного поиска, BM25-индексации и статистического анализа IQR. Обеспечиваем поиск релеватных котировок и точную фильтрацию выбросов.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link 
              href="/catalog" 
              className="bg-portal-blue text-white px-8 py-4 rounded font-bold hover:bg-portal-blue-hover transition-all shadow-md hover:shadow-lg active:scale-95 flex items-center gap-2"
            >
              Перейти в каталог
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
            </Link>
          </div>
        </div>
      </section>

      {/* Stats/Quick Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white border border-border-portal p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow border-l-4 border-l-portal-blue">
          <div className="text-xs font-bold text-text-muted uppercase mb-2 tracking-widest">Проверено СТЕ</div>
          <div className="text-3xl font-black text-text-main">240к+</div>
          <div className="text-xs text-portal-green font-bold mt-2">Выборка ЕАИСТ (Хакатон)</div>
        </div>
        <div className="bg-white border border-border-portal p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow border-l-4 border-l-portal-green">
          <div className="text-xs font-bold text-text-muted uppercase mb-2 tracking-widest">Методология</div>
          <div className="text-3xl font-black text-text-main">IQR + BM25</div>
          <div className="text-xs text-text-muted font-bold mt-2">Очистка от экстремальных цен</div>
        </div>
        <div className="bg-white border border-border-portal p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow border-l-4 border-l-portal-red">
          <div className="text-xs font-bold text-text-muted uppercase mb-2 tracking-widest">Корреляция</div>
          <div className="text-3xl font-black text-text-main">Vector Match</div>
          <div className="text-xs text-portal-red font-bold mt-2">Точный поиск аналогов</div>
        </div>
      </div>

      {/* Features Grid */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-4">
        <div className="flex flex-col gap-6">
          <h2 className="text-2xl font-black text-text-main tracking-tight flex items-center gap-3">
            <span className="w-8 h-1 bg-portal-blue rounded-full" />
            Основные инструменты
          </h2>
          
          <div className="grid grid-cols-1 gap-4">
            <div className="bg-white border border-border-portal p-6 rounded-lg hover:border-portal-blue/30 transition-colors group cursor-default">
              <div className="flex items-start gap-4">
                <div className="bg-portal-blue/10 p-3 rounded-lg text-portal-blue">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                </div>
                <div>
                  <h3 className="font-black text-text-main mb-1 group-hover:text-portal-blue transition-colors">Гибридный поиск (BM25 + Vector)</h3>
                  <p className="text-sm text-text-muted leading-relaxed">Поиск сопоставимых позиций на базе векторных эмбеддингов и алгоритма BM25. Поддержка регулярных выражений (Regexp) и индексации в PostgreSQL для максимальной точности.</p>
                </div>
              </div>
            </div>

            <div className="bg-white border border-border-portal p-6 rounded-lg hover:border-portal-green/30 transition-colors group cursor-default">
              <div className="flex items-start gap-4">
                <div className="bg-portal-green/10 p-3 rounded-lg text-portal-green">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                </div>
                <div>
                  <h3 className="font-black text-text-main mb-1 group-hover:text-portal-green transition-colors">Статистический расчет (Smart Price)</h3>
                  <p className="text-sm text-text-muted leading-relaxed">Автоматическая фильтрация аномальных цен методом IQR (межквартильный размах). Расчет медианного значения и поправочных коэффициентов.</p>
                </div>
              </div>
            </div>

            <div className="bg-white border border-border-portal p-6 rounded-lg hover:border-portal-red/30 transition-colors group cursor-default">
              <div className="flex items-start gap-4">
                <div className="bg-portal-red/10 p-3 rounded-lg text-portal-red">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                </div>
                <div>
                  <h3 className="font-black text-text-main mb-1 group-hover:text-portal-red transition-colors">Автоматическое обоснование</h3>
                  <p className="text-sm text-text-muted leading-relaxed">Мгновенная выгрузка готовых DOCX-отчетов, полностью соответствующих регламентам Портала Поставщиков Москвы.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-portal-blue rounded-lg p-8 text-white relative flex flex-col justify-center overflow-hidden">
          <div className="absolute top-0 right-0 w-full h-full opacity-10 pointer-events-none">
            <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
              <defs><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="1"/></pattern></defs>
              <rect width="100%" height="100%" fill="url(#grid)" />
            </svg>
          </div>
          <h2 className="text-3xl font-black mb-6 relative">Эффективность <br />и точность</h2>
          <p className="text-portal-blue-light mb-8 opacity-90 leading-relaxed text-lg">
            Алгоритм учитывает региональные коэффициенты, сроки давности контрактов и специфику характеристик СТЕ.
          </p>
          <div className="flex flex-col gap-3">
             <div className="flex items-center gap-3 bg-white/10 p-3 rounded backdrop-blur-sm border border-white/20">
                <div className="w-2 h-2 rounded-full bg-white" />
                <span className="text-sm font-bold">Интеграция с базой данных ЕАИСТ</span>
             </div>
             <div className="flex items-center gap-3 bg-white/10 p-3 rounded backdrop-blur-sm border border-white/20">
                <div className="w-2 h-2 rounded-full bg-portal-green" />
                <span className="text-sm font-bold">Обновление котировок в реальном времени</span>
             </div>
          </div>
        </div>
      </section>

      {/* Footer-like note */}
      <footer className="mt-8 pt-8 border-t border-border-portal flex flex-col md:flex-row justify-between items-center text-text-muted gap-4 text-[10px] font-bold uppercase tracking-widest">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-portal-red rounded-sm" />
          <span className="italic">Tender Hack Team 2026</span>
        </div>
        <div className="flex gap-6">
          <a href="#" className="hover:text-portal-blue transition-colors">Методология</a>
          <a href="#" className="hover:text-portal-blue transition-colors">API Docs</a>
          <a href="#" className="hover:text-portal-blue transition-colors">Поддержка</a>
        </div>
      </footer>
    </div>
  );
}
