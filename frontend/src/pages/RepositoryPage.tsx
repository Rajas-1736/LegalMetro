import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';
import { Product, ProductHistoryItem } from '../types';
import { 
  Search, Filter, Package, Calendar, Eye, CheckCircle2, 
  XCircle, AlertTriangle, History, ArrowRight, ShieldCheck 
} from 'lucide-react';

interface RepositoryPageProps {
  onViewReport: (scanId: string) => void;
  onInspectProduct: () => void;
}

const CATEGORIES = [
  'ALL',
  'Packaged Food',
  'Beverages & Oils',
  'Cosmetics & Toiletries',
  'Household Chemicals',
  'Imported Goods',
  'Consumer Electronics',
];

export const RepositoryPage: React.FC<RepositoryPageProps> = ({ onViewReport, onInspectProduct }) => {
  const { t } = useTranslation();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');

  const STATUS_FILTERS = [
    { id: 'ALL', label: t('repository.filter_status') },
    { id: 'COMPLIANT', label: t('status.compliant') },
    { id: 'NON_COMPLIANT', label: t('status.non_compliant') },
    { id: 'FLAGGED_FOR_REVIEW', label: t('status.needs_review') },
  ];

  // History modal
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [historyItems, setHistoryItems] = useState<ProductHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const data = await api.products.list({
        search: search || undefined,
        category: selectedCategory !== 'ALL' ? selectedCategory : undefined,
        status: selectedStatus !== 'ALL' ? selectedStatus : undefined,
      });
      setProducts(data);
    } catch (err) {
      console.error('Failed to load products', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [selectedCategory, selectedStatus]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchProducts();
  };

  const openHistory = async (prod: Product) => {
    setSelectedProduct(prod);
    setLoadingHistory(true);
    try {
      const data = await api.products.getHistory(prod.id);
      setHistoryItems(data.inspections);
    } catch (err) {
      console.error('Failed to fetch history', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLIANT':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> {t('status.compliant')}
          </span>
        );
      case 'NON_COMPLIANT':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 border border-rose-200">
            <XCircle className="w-3 h-3 text-rose-600" /> {t('status.non_compliant')}
          </span>
        );
      case 'FLAGGED_FOR_REVIEW':
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
            <AlertTriangle className="w-3 h-3 text-amber-600" /> {t('status.needs_review')}
          </span>
        );
      default:
        return (
          <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <Package className="w-5 h-5 text-blue-600" />
            <span>{t('repository.title')}</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {t('repository.subtitle')}
          </p>
        </div>

        <button
          onClick={onInspectProduct}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow transition flex items-center gap-1.5 self-start cursor-pointer"
        >
          <span>{t('repository.btn_inspect')}</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t('repository.search_placeholder')}
              className="w-full text-xs pl-9 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition cursor-pointer"
          >
            {t('common.search')}
          </button>
        </form>

        {/* Category Pills */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <span className="text-[11px] font-bold text-slate-500 mr-1 flex items-center gap-1">
            <Filter className="w-3 h-3" /> {t('common.category')}:
          </span>
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`text-xs px-2.5 py-1 rounded-full transition font-medium cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-blue-600 text-white font-semibold shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {cat === 'ALL' ? t('common.all') : cat}
            </button>
          ))}
        </div>

        {/* Status Filters */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1 border-t border-slate-100">
          <span className="text-[11px] font-bold text-slate-500 mr-1">{t('common.status')}:</span>
          {STATUS_FILTERS.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelectedStatus(s.id)}
              className={`text-xs px-2.5 py-1 rounded-full transition font-medium cursor-pointer ${
                selectedStatus === s.id
                  ? 'bg-slate-800 text-white font-semibold'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Products Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400">Loading product repository...</div>
        ) : products.length === 0 ? (
          <div className="p-12 sm:p-16 text-center max-w-md mx-auto space-y-4">
            {/* Custom SVG Metrology Inspection Empty State Illustration */}
            <div className="w-24 h-24 mx-auto relative flex items-center justify-center">
              <div className="w-20 h-20 rounded-2xl bg-slate-100 border border-slate-200 flex items-center justify-center shadow-inner">
                <svg className="w-10 h-10 text-slate-400" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M8 14L24 6L40 14L24 22L8 14Z" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="#f8fafc" />
                  <path d="M8 14V34L24 42V22" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M40 14V34L24 42" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M16 10L32 18" stroke="#3b82f6" strokeWidth="2" strokeDasharray="3 3" />
                  <circle cx="36" cy="36" r="8" fill="#3b82f6" fillOpacity="0.15" stroke="#2563eb" strokeWidth="2" />
                  <path d="M34 36L36 38L39 34" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <div className="absolute -bottom-1 -right-1 w-7 h-7 bg-blue-600 text-white rounded-full flex items-center justify-center shadow-md">
                <Search className="w-3.5 h-3.5" />
              </div>
            </div>

            <div className="space-y-1">
              <h4 className="text-sm font-bold text-slate-800">No Packaging Records Found</h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                {search || selectedCategory !== 'ALL' || selectedStatus !== 'ALL'
                  ? 'No products matched your current search filters. Try clearing or adjusting search terms.'
                  : 'Your enforcement database does not have any scanned commodities yet. Start a scan to create auditable records.'}
              </p>
            </div>

            <div className="pt-2 flex items-center justify-center gap-3">
              {(search || selectedCategory !== 'ALL' || selectedStatus !== 'ALL') ? (
                <button
                  type="button"
                  onClick={() => {
                    setSearch('');
                    setSelectedCategory('ALL');
                    setSelectedStatus('ALL');
                  }}
                  className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-lg transition"
                >
                  Reset Filters
                </button>
              ) : null}
              <button
                type="button"
                onClick={onInspectProduct}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs rounded-xl shadow-md shadow-blue-600/20 transition flex items-center space-x-1.5 cursor-pointer"
              >
                <span>{t('repository.btn_inspect')}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto w-full">
            <table className="w-full text-left text-xs border-collapse min-w-[640px]">
              <thead className="bg-slate-50 text-slate-600 border-b border-slate-200 uppercase font-bold text-[10px] tracking-wider">
                <tr>
                  <th className="p-3.5">{t('repository.col_product')}</th>
                  <th className="p-3.5">{t('common.category')}</th>
                  <th className="p-3.5">{t('repository.col_qty_mrp')}</th>
                  <th className="p-3.5">MRP</th>
                  <th className="p-3.5">{t('repository.col_status')}</th>
                  <th className="p-3.5">Inspections</th>
                  <th className="p-3.5 text-right">{t('repository.col_actions')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {products.map((prod) => (
                  <tr key={prod.id} className="hover:bg-slate-50/70 transition">
                    <td className="p-3.5">
                      <div className="font-bold text-slate-900">{prod.product_name}</div>
                      <div className="text-[10px] text-slate-500 truncate max-w-xs">{prod.manufacturer_name || 'Manufacturer on file'}</div>
                    </td>
                    <td className="p-3.5 text-slate-600">
                      <span className="bg-slate-100 px-2 py-0.5 rounded text-[11px]">{prod.category}</span>
                    </td>
                    <td className="p-3.5 font-mono text-slate-700">{prod.declared_net_quantity || '—'}</td>
                    <td className="p-3.5 font-mono text-slate-700">{prod.declared_mrp || '—'}</td>
                    <td className="p-3.5">{getStatusBadge(prod.latest_compliance_status)}</td>
                    <td className="p-3.5 font-mono font-bold text-slate-700">{prod.inspection_count}</td>
                    <td className="p-3.5 text-right">
                      <button
                        onClick={() => openHistory(prod)}
                        className="inline-flex items-center space-x-1 text-xs text-blue-600 hover:text-blue-800 font-semibold p-1 rounded hover:bg-blue-50 cursor-pointer"
                      >
                        <History className="w-3.5 h-3.5" />
                        <span>{t('repository.btn_view_history')}</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Product Inspection History Drawer/Modal */}
      {selectedProduct && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-6 space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-start justify-between border-b pb-3">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">{t('repository.history_drawer_title')}</span>
                <h3 className="font-extrabold text-base text-slate-900">{selectedProduct.product_name}</h3>
                <p className="text-xs text-slate-500">{selectedProduct.category} • {selectedProduct.manufacturer_name}</p>
              </div>
              <button
                onClick={() => setSelectedProduct(null)}
                className="text-slate-400 hover:text-slate-600 text-lg p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {loadingHistory ? (
                <div className="p-8 text-center text-xs text-slate-400">{t('common.loading')}</div>
              ) : historyItems.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-400">No previous inspection scans logged for this product.</div>
              ) : (
                historyItems.map((item) => (
                  <div key={item.scan_id} className="p-3 rounded-lg border border-slate-200 bg-slate-50/50 flex items-center justify-between gap-4">
                    <div className="flex items-center space-x-3 min-w-0">
                      <img
                        src={item.image_url}
                        alt="Label"
                        className="w-12 h-12 object-cover rounded border border-slate-200 shrink-0"
                      />
                      <div className="min-w-0">
                        <div className="flex items-center space-x-2">
                          {getStatusBadge(item.overall_compliance_verdict)}
                          <span className="text-[11px] font-mono text-slate-400">{t('common.score')}: {item.compliance_score}%</span>
                        </div>
                        <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-2">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" /> {new Date(item.created_at).toLocaleDateString()}
                          </span>
                          <span>•</span>
                          <span>Inspector: {item.inspector_name || 'Enforcement Officer'}</span>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => {
                        setSelectedProduct(null);
                        onViewReport(item.scan_id);
                      }}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold shrink-0 transition cursor-pointer"
                    >
                      {t('common.view_report')}
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="pt-2 border-t text-right">
              <button
                onClick={() => setSelectedProduct(null)}
                className="px-4 py-1.5 rounded-lg border text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
              >
                {t('common.close')}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
